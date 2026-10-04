# pyrefly: ignore [missing-import]
from panda3d.core import loadPrcFileData
loadPrcFileData("", 
"""
textures-power-2 None
bullet-filter-algorithm groups-mask
bullet-enable-contact-events true
""")

from direct.showbase.ShowBase import ShowBase
import simplepbr
import gltf
from ctypes import windll
import os
import sys
import pathlib
# プロジェクトのルートディレクトリ（基準パス）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from direct.filter.FilterManager import FilterManager, FrameBufferProperties
from table_animator.shared.util.yamane_prepare import *
from table_animator.shared.util.path_manager import PathManager
from table_animator.core.core_system import CoreSystem
from table_animator.graphics.resource_context import ResourceContext


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        if self.loader is None:
            return        

        pipeline = simplepbr.init(exposure=0, use_normal_maps=True)
        #LUT stuff
        #self.manager=FilterManager(self.win, self.cam)    
        self.manager = pipeline._filtermgr
        #self.setupLUT('./resource/lut/contrast_up.png')        
        self.color_grading()
        #self.render.set_shader_auto()






        self.properties = WindowProperties()
        self.properties.setTitle("Marble Allocator")

        self.accept("space", self.oobe)
        self.disableMouse()

        if self.loader is None:
            return
        self.axis: NodePath = self.loader.loadModel("models/zup-axis")
        self.axis.setPos(0, 0, 0)
        self.axis.setScale((1, 1, 1))

        is_debug = False
        if is_debug:
            self.properties.setSize(1280, 720)
            self.setFrameRateMeter(True)
            #self.setSceneGraphAnalyzerMeter(True)
            self.axis.reparentTo(self.render)
        else:
            self.properties.setSize(1280, 720)

        self.properties.setFixedSize(True)


        if self.win is not None:
            self.win.requestProperties(self.properties)


        lens = self.camLens
        lens.setNear(2)   # 近クリップ
        lens.setFar(2000.0)  # 遠クリップ
        lens.setFov(30)
        self.camera.setPos(120, -120, 120)
        self.camera.setHpr(45, -30, 0)


        self.__resource_context = ResourceContext(self)
        self.__core_system = CoreSystem(self)


        self.taskMgr.add(self.__update, "update_master")
        self.accept("q", self.debug_analyze)
        self.accept("s", self.debug_screenshot)



    @property
    def resource_context(self):
        return self.__resource_context

    def debug_screenshot(self):
        self.movie(namePrefix='image', duration=1, fps=1, format='png')
        logger.info("screen_shot")

    def debug_analyze(self):
        self.render.analyze()

    def color_grading(self):
        fbprops = FrameBufferProperties()
        fbprops.setFloatColor(True)  # 16bit float

        colortex = Texture()
        self.quad = self.manager.renderSceneInto(colortex=colortex, fbprops=fbprops)
        if self.quad is None:
            return
        self.quad.setShader(Shader.load(Shader.SLGLSL, PathManager.resource_vfs("shaders/color_grading_v.glsl"), PathManager.resource_vfs("shaders/color_grading_f.glsl")))
        self.quad.setShaderInput("colortex", colortex)
    
    def __update(self, task: Task.Task):
        frame_time = globalClock.getFrameTime()
        dt = globalClock.getDt()
        self.__core_system.update(frame_time, dt)
        return task.cont


if __name__ == "__main__":
    print(f"Current Directory: {os.getcwd()}")
    print(f"sys.path[0]: {sys.path[0]}")
    print(f"sys.path: {sys.path}")
    print(f"Python Version: {sys.version}")
    print(f"Panda3D Version: {PandaSystem.getVersionString()}")
    windll.winmm.timeBeginPeriod(1)
    globalClock.setMode(ClockObject.M_limited)
    globalClock.setFrameRate(24)
    app = MyApp()
    app.run()
    windll.winmm.timeEndPeriod(1)
    logger.info("終了")