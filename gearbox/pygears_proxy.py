import os
import runpy
import functools
import threading
import queue
import time
import sys
from PySide2 import QtCore, QtWidgets
from pygears.conf import Inject, reg_inject, safe_bind, bind, PluginBase, registry, config
from pygears.sim.extens.sim_extend import SimExtend
from .node_model import find_cosim_modules
from pygears.sim.modules import SimVerilated
from pygears.sim import sim, SimFinish
from pygears import clear
from pygears.sim.extens.vcd import VCD


class Gearbox(SimExtend):
    def __init__(self,
                 top=None,
                 live=True,
                 reload=True,
                 standalone=False,
                 sim_queue=None):

        super().__init__(top)

        bind('sim/gearbox', self)

        self.queue = sim_queue
        if self.queue is None:
            self.queue = queue.Queue()

        self.live = live
        self.done = False
        self.reload = reload
        self.standalone = standalone

    def handle_event(self, name):
        self.queue.put(name)
        self.queue.join()

        if self.done:
            self.done = False
            raise SimFinish
            # sys.exit(0)

        # Let GUI thread do some work
        time.sleep(0.0001)

    @reg_inject
    def before_run(self, sim, outdir=Inject('sim/artifact_dir')):
        if self.live and not self.standalone:
            registry('gearbox/layers').insert(0, sim_bridge)
            thread = threading.Thread(target=main)
            thread.start()

        self.handle_event('before_run')

    def at_exit(self, sim):
        self.handle_event('at_exit')

    def after_timestep(self, sim, timestep):
        # if timestep > (1 << 15):
        self.handle_event('after_timestep')
        return True

    def after_run(self, sim):
        self.handle_event('after_run')

    def before_setup(self, sim):
        if self.live:
            for m in find_cosim_modules():
                if isinstance(m, SimVerilated):
                    m.vcd_fifo = True
                    m.shmidcat = True

    # def after_cleanup(self, sim):
    #     if not self.live:
    #         main()


def sim_bridge():
    sim_bridge = PyGearsClient()
    safe_bind('gearbox/sim_bridge', sim_bridge)
    return sim_bridge


class PyGearsProc(QtCore.QObject):
    def __init__(self):
        super().__init__()

        self.thrd = QtCore.QThread()
        self.moveToThread(self.thrd)
        self.thrd.started.connect(self.run)

        self.queue = queue.Queue()
        self.plugin = functools.partial(
            Gearbox, standalone=True, sim_queue=self.queue)

        self.thrd.start()

    def run(self):
        try:
            sim(outdir='build', extens=[VCD, self.plugin])
        except Exception:
            import traceback
            traceback.print_exc()

        self.thrd.quit()


class PyGearsClient(QtCore.QObject):
    model_closed = QtCore.Signal()
    model_loaded = QtCore.Signal()
    sim_started = QtCore.Signal()
    after_run = QtCore.Signal()
    after_timestep = QtCore.Signal()
    sim_refresh = QtCore.Signal()
    message = QtCore.Signal(str)

    @reg_inject
    def __init__(
            self,
            parent=None,
            standalone=False,
    ):
        super().__init__(parent)

        self.loop = QtCore.QEventLoop(self)
        self.breakpoints = set()
        self.running = False
        self.invoke_queue = queue.Queue()
        self.queue = None
        self.closing = False

        QtWidgets.QApplication.instance().aboutToQuit.connect(self.quit)
        self.start_thread()

    def start_thread(self):
        self.thrd = QtCore.QThread()
        self.moveToThread(self.thrd)
        self.loop.moveToThread(self.thrd)
        self.thrd.started.connect(self.run)
        self.thrd.start()

    def invoke_method(self, name, *args, **kwds):
        self.invoke(getattr(self, name), *args, **kwds)

    def invoke(self, func, *args, **kwds):
        self.invoke_queue.put(functools.partial(func, *args, **kwds))

        QtCore.QMetaObject.invokeMethod(self, "invoke_handler",
                                        QtCore.Qt.QueuedConnection)

    @QtCore.Slot()
    def invoke_handler(self):
        f = self.invoke_queue.get()
        f()

    def run_sim(self):
        print("Running sim")
        self.pygears_proc = PyGearsProc()
        self.queue = self.pygears_proc.queue
        print("Sim run")

    def close_model(self):
        if registry('gearbox/model_script_name'):
            bind('gearbox/model_script_name', None)
            if self.queue is not None:
                registry('sim/gearbox').done = True
                self.closing = True
                self.cont()
            else:
                self.model_closed.emit()
                # self.queue = None
            # self.loop.quit()

    def run_model(self, script_fn):
        gearbox_registry = registry('gearbox')
        clear()
        bind('gearbox', gearbox_registry)
        bind('sim/artifact_dir',
             os.path.join(os.path.dirname(script_fn), 'build'))

        sys.path.append(os.path.dirname(script_fn))
        config['trace/ignore'].append(os.path.dirname(__file__))
        config['trace/ignore'].append(runpy.__file__)
        runpy.run_path(script_fn)
        bind('gearbox/model_script_name', script_fn)
        self.model_loaded.emit()

    def cont(self):
        QtCore.QMetaObject.invokeMethod(self.loop, 'quit',
                                        QtCore.Qt.AutoConnection)

    def _should_break(self):
        triggered = False
        discard = []

        for b in self.breakpoints:
            trig, keep = b()
            if trig:
                triggered = True

            if not keep:
                discard.append(b)

        self.breakpoints.difference_update(discard)

        return triggered

    def queue_loop(self):
        while self.queue is not None:

            self.thrd.eventDispatcher().processEvents(
                QtCore.QEventLoop.AllEvents)

            try:
                msg = self.queue.get(0.001)
            except queue.Empty:
                if registry('gearbox/model_script_name') is None:
                    print("HERE?")
                    self.queue = None
                    return
                else:
                    continue

            if msg == "after_timestep":
                self.after_timestep.emit()
                if self._should_break():
                    self.running = False
                    self.sim_refresh.emit()
                    self.loop.exec_()
            elif msg == "after_run":
                if not self.closing:
                    self.sim_refresh.emit()
                    self.after_run.emit()

                # self.queue.task_done()
                # self.queue = None
                # self.closing = False
                # return

            elif msg == "at_exit":
                if self.closing:
                    self.model_closed.emit()

                # self.quit()
                self.queue.task_done()
                self.queue = None
                self.closing = False
                return
            elif msg == "before_run":
                self.sim_started.emit()
                self.running = False
                self.loop.exec_()
                self.running = True

            if self.queue:
                self.queue.task_done()

    def run(self):
        while True:
            while self.queue is None:
                self.thrd.eventDispatcher().processEvents(
                    QtCore.QEventLoop.AllEvents)
                time.sleep(0.1)

            try:
                self.queue_loop()
            except Exception:
                import traceback
                traceback.print_exc()

    def quit(self):
        # self.plugin.done = True
        self.thrd.quit()

    def refresh_timeout(self):
        self.sim_refresh.emit()


class MainWindowPlugin(PluginBase):
    @classmethod
    def bind(cls):
        safe_bind('gearbox/model_script_name', None)
