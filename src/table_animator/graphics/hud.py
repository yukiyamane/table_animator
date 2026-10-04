from __future__ import annotations
import math
import random
from direct.gui.DirectGui import DirectWaitBar, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.IntervalGlobal import Sequence, LerpFunctionInterval, Func


from typing import Optional
from dataclasses import dataclass
from table_animator.shared.util.yamane_prepare import *
from table_animator.shared.util.path_manager import PathManager
from table_animator.graphics.setting import marble_graphics_setting_list

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from table_animator.main import MyApp


from direct.gui.DirectGui import DirectFrame, OnscreenImage, OnscreenText
# pyrefly: ignore [missing-import]
from panda3d.core import TransparencyAttrib, Point3, TextNode
from direct.interval.IntervalGlobal import Sequence, LerpFunctionInterval, LerpScaleInterval, Parallel, Wait

class HUD:
    def __init__(self, base):
        self.__base = base

        self.__frame = DirectFrame(
            frameColor=(0.03, 0.08, 0.12, 1.0),
            frameSize=(-1.8, 1.8, -1.0, 1.0),
            pos=(0, 0, 0),
            parent=base.aspect2d
        )
        self.__frame.setBin("fixed", -10)
        self.__frame.setDepthTest(False)
        self.__frame.setDepthWrite(False)
        
        self.__tournament_ui = TournamentUI(base)

    def start(self):
        self.__tournament_ui.start()

    def update(self):
        self.__tournament_ui.update()


class TournamentUI:
    def __init__(self, base):
        self.__base = base
        self.__tournament_lines_ui = TournamentLinesUI(base)
        
        # 1回戦枠 (0: P0, 1: P1, 2: P2, 3: P3)
        self.__player_ui_list = [TournamentPlayerUI(base, i) for i in range(4)]
        
        # 決勝戦枠 (4: M0(上), 5: M1(下), 6: Winner)
        self.__final_ui_m0 = TournamentPlayerUI(base, 4, is_final=True)
        self.__final_ui_m1 = TournamentPlayerUI(base, 5, is_final=True)
        self.__final_ui_winner = TournamentPlayerUI(base, 6, is_final=True)

        self.__process_sequence = None
        self.__confetti = None

    def start(self):
        # 全試合を連続でアニメーション演出しながら進行するテスト
        self.set_match_state([0, 2, 0])

    def stop_process(self):
        """実行中の進行アニメーションを停止"""
        if self.__process_sequence and self.__process_sequence.isPlaying():
            self.__process_sequence.finish()
            self.__process_sequence = None

        if self.__confetti:
            self.__confetti.stop()
            self.__confetti = None

    def start_confetti(self, winner_index: int):
        """紙吹雪を開始するヘルパーメソッド"""
        self.__confetti = Confetti(self.__base, winner_index)
        self.__confetti.start()

    def set_match_state(self, match_results: list):
        """
        試合状況（[試合1勝者, 試合2勝者, 決勝勝者]）に応じて順を追って演出を実行
        """
        self.stop_process()

        m1_winner = match_results[0] if len(match_results) > 0 else None
        m2_winner = match_results[1] if len(match_results) > 1 else None
        final_winner = match_results[2] if len(match_results) > 2 else None

        # 初期化：すべての暗転・ハイライトをリセット
        for ui in self.__player_ui_list:
            ui.set_dark(False)
            ui.stop_highlight()
        self.__final_ui_m0.set_dark(False)
        self.__final_ui_m0.stop_highlight()
        self.__final_ui_m1.set_dark(False)
        self.__final_ui_m1.stop_highlight()
        self.__final_ui_winner.set_dark(False)
        self.__final_ui_winner.stop_highlight()
        self.__tournament_lines_ui.clear_red_lines()

        # 一連のシーケンス作成
        seq = Sequence()

        # ----------------------------------------------------
        # 初期状態: 第1試合のハイライト
        # ----------------------------------------------------
        seq.append(Func(self.__player_ui_list[0].start_highlight))
        seq.append(Func(self.__player_ui_list[1].start_highlight))

        # ----------------------------------------------------
        # 第1試合の結果処理
        # ----------------------------------------------------
        if m1_winner in [0, 1]:
            loser0 = 1 if m1_winner == 0 else 0
            seq.append(Func(self.__player_ui_list[0].stop_highlight))
            seq.append(Func(self.__player_ui_list[1].stop_highlight))

            # 1. 敗者が暗くなる
            seq.append(Func(self.__player_ui_list[loser0].set_dark, True))
            seq.append(Wait(0.2))

            # 2. 線が動く
            seq.append(self.__tournament_lines_ui.create_match_anim(m1_winner, 0))

            # 3. 勝利位置のプレイヤー名を表示
            seq.append(Func(self.__final_ui_m0.copy_from, self.__player_ui_list[m1_winner]))

            # 4. 1秒待機
            seq.append(Wait(1.0))

            # 5. 次の試合のハイライト（第2試合が未完了の場合）
            if m2_winner is None:
                seq.append(Func(self.__player_ui_list[2].start_highlight))
                seq.append(Func(self.__player_ui_list[3].start_highlight))

        # ----------------------------------------------------
        # 第2試合の結果処理
        # ----------------------------------------------------
        if m2_winner in [2, 3]:
            loser1 = 3 if m2_winner == 2 else 2
            seq.append(Func(self.__player_ui_list[2].stop_highlight))
            seq.append(Func(self.__player_ui_list[3].stop_highlight))

            # 1. 敗者が暗くなる
            seq.append(Func(self.__player_ui_list[loser1].set_dark, True))
            seq.append(Wait(0.2))

            # 2. 線が動く
            seq.append(self.__tournament_lines_ui.create_match_anim(m2_winner, 1))

            # 3. 勝利位置のプレイヤー名を表示
            seq.append(Func(self.__final_ui_m1.copy_from, self.__player_ui_list[m2_winner]))

            # 4. 1秒待機
            seq.append(Wait(1.0))

            # 5. 次の試合のハイライト（決勝が未完了の場合）
            if final_winner is None:
                seq.append(Func(self.__final_ui_m0.start_highlight))
                seq.append(Func(self.__final_ui_m1.start_highlight))

        # ----------------------------------------------------
        # 決勝戦の結果処理
        # ----------------------------------------------------
        if final_winner in [0, 1, 2, 3]:
            seq.append(Func(self.__final_ui_m0.stop_highlight))
            seq.append(Func(self.__final_ui_m1.stop_highlight))

            # 1. 敗者が暗くなる
            if final_winner in [0, 1]:
                seq.append(Func(self.__final_ui_m1.set_dark, True))
                target_ui = self.__final_ui_m0
            else:
                seq.append(Func(self.__final_ui_m0.set_dark, True))
                target_ui = self.__final_ui_m1
            seq.append(Wait(0.2))

            # 2. 線が動く
            seq.append(self.__tournament_lines_ui.create_final_anim(final_winner))

            # 3. 勝利位置（優勝者）のプレイヤー名を表示
            seq.append(Func(self.__final_ui_winner.copy_from, target_ui))

            # 4. 1秒待機
            seq.append(Wait(1.0))

            # 5. 優勝枠ハイライト ＆ 紙吹雪の生成開始！
            seq.append(Func(self.__final_ui_winner.start_highlight))
            seq.append(Func(self.start_confetti, final_winner))

        self.__process_sequence = seq
        self.__process_sequence.start()

    def update(self):
        self.__tournament_lines_ui.update()
        # 紙吹雪の更新ルーチンを呼ぶ
        if self.__confetti:
            self.__confetti.update()

class TournamentLinesUI:
    def __init__(self, base):
        self.__base = base
        self.__node_path = base.aspect2d.attachNewNode("tournament_lines")
        self.line_t = 0.01

        self.x0 = -1.0
        self.x1 = -0.5
        self.x2 = 0.0
        self.x3 = 0.5
        self.x4 = 1.0

        self.z_p = [0.75, 0.25, -0.25, -0.75]
        self.z_m = [(self.z_p[0] + self.z_p[1]) / 2, (self.z_p[2] + self.z_p[3]) / 2]
        self.z_final = 0.0

        self._create_base_lines()
        self.__current_anim = None
        self.__red_frames = []

        self.__trophy = OnscreenImage(
            image=PathManager.resource_vfs("textures/hud/trophy.png"),
            pos=(self.x4 + 0.3, 0, self.z_final),
            parent=self.__node_path,
            scale=0.2,
            color=(1, 1, 0.2, 1)
        )
        self.__node_path.setBin("fixed", 0)
        self.__trophy.setTransparency(TransparencyAttrib.MAlpha)

    def _create_h_line(self, x_start: float, x_end: float, z: float, color=(1, 1, 1, 1)) -> DirectFrame:
        return DirectFrame(
            frameColor=color,
            frameSize=(0, x_end - x_start, -self.line_t, self.line_t),
            pos=(x_start, 0, z),
            parent=self.__node_path
        )

    def _create_v_line(self, x: float, z_start: float, z_end: float, color=(1, 1, 1, 1)) -> DirectFrame:
        return DirectFrame(
            frameColor=color,
            frameSize=(-self.line_t, self.line_t, z_end - z_start, 0),
            pos=(x, 0, z_start),
            parent=self.__node_path
        )

    def _create_base_lines(self):
        for z in self.z_p:
            self._create_h_line(self.x0, self.x1, z)
        self._create_v_line(self.x1, self.z_p[0], self.z_p[1])
        self._create_v_line(self.x1, self.z_p[2], self.z_p[3])

        self._create_h_line(self.x1, self.x2, self.z_m[0])
        self._create_h_line(self.x1, self.x2, self.z_m[1])
        self._create_v_line(self.x3, self.z_m[0], self.z_m[1])
        self._create_h_line(self.x2, self.x3, self.z_m[0])
        self._create_h_line(self.x2, self.x3, self.z_m[1])

        self._create_h_line(self.x3, self.x4, self.z_final)

    def clear_red_lines(self):
        if self.__current_anim and self.__current_anim.isPlaying():
            self.__current_anim.finish()
        for f in self.__red_frames:
            f.destroy()
        self.__red_frames.clear()

    def create_match_anim(self, winner_idx: int, match_num: int, duration_per_segment: float = 0.25) -> Sequence:
        """1回戦（第1試合/第2試合）の線伸長アニメーションをSequenceとして作成"""
        red = (1, 0.2, 0.2, 1)
        sub_seq = Sequence()

        def add_h_anim(x_start, x_end, z):
            frame = self._create_h_line(x_start, x_start, z, color=red)
            self.__red_frames.append(frame)
            def set_size(t):
                curr_x = x_start + (x_end - x_start) * t
                frame['frameSize'] = (0, curr_x - x_start, -self.line_t, self.line_t)
            return LerpFunctionInterval(set_size, duration=duration_per_segment)

        def add_v_anim(x, z_start, z_end):
            frame = self._create_v_line(x, z_start, z_start, color=red)
            self.__red_frames.append(frame)
            def set_size(t):
                curr_z = z_start + (z_end - z_start) * t
                frame['frameSize'] = (-self.line_t, self.line_t, curr_z - z_start, 0)
            return LerpFunctionInterval(set_size, duration=duration_per_segment)

        target_z = self.z_m[match_num]
        sub_seq.append(add_h_anim(self.x0, self.x1, self.z_p[winner_idx]))
        sub_seq.append(add_v_anim(self.x1, self.z_p[winner_idx], target_z))
        sub_seq.append(add_h_anim(self.x1, self.x2, target_z))

        return sub_seq

    def create_final_anim(self, final_winner_idx: int, duration_per_segment: float = 0.25) -> Sequence:
        """決勝戦の線伸長アニメーションをSequenceとして作成"""
        red = (1, 0.2, 0.2, 1)
        sub_seq = Sequence()

        def add_h_anim(x_start, x_end, z):
            frame = self._create_h_line(x_start, x_start, z, color=red)
            self.__red_frames.append(frame)
            def set_size(t):
                curr_x = x_start + (x_end - x_start) * t
                frame['frameSize'] = (0, curr_x - x_start, -self.line_t, self.line_t)
            return LerpFunctionInterval(set_size, duration=duration_per_segment)

        def add_v_anim(x, z_start, z_end):
            frame = self._create_v_line(x, z_start, z_start, color=red)
            self.__red_frames.append(frame)
            def set_size(t):
                curr_z = z_start + (z_end - z_start) * t
                frame['frameSize'] = (-self.line_t, self.line_t, curr_z - z_start, 0)
            return LerpFunctionInterval(set_size, duration=duration_per_segment)

        m_idx = 0 if final_winner_idx in [0, 1] else 1
        sub_seq.append(add_h_anim(self.x2, self.x3, self.z_m[m_idx]))
        sub_seq.append(add_v_anim(self.x3, self.z_m[m_idx], self.z_final))
        sub_seq.append(add_h_anim(self.x3, self.x4, self.z_final))

        return sub_seq

    def update(self):
        pass


class TournamentPlayerUI:
    def __init__(self, base, index: int, is_final: bool = False):
        self.__base = base
        self.__index = index
        self.__node_path = base.aspect2d.attachNewNode("tournament_player_ui")
        self.__anim = None
        self.__color = (1, 1, 1, 1)  # プレイヤーカラー保持用

        # 位置の定義（0~3:1回戦, 4:準決勝上, 5:準決勝下, 6:優勝枠）
        pos_list = [
            Point3(-1.25, 0, 0.75), Point3(-1.25, 0, 0.25),
            Point3(-1.25, 0, -0.25), Point3(-1.25, 0, -0.75),
            Point3(-0.25, 0, 0.50), Point3(-0.25, 0, -0.50), # 準決勝
            Point3(0.75, 0, 0.00)                             # 優勝
        ]
        self.__node_path.setPos(pos_list[index])
        
        # 1. 最背面：色の矩形（外枠縁取り用）
        self.__color_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),  # 初期は透明
            frameSize=(-0.27, 0.27, -0.12, 0.12),
            pos=(0, 0, 0),
            parent=self.__node_path
        )
        self.__color_frame.setBin("fixed", 0)
        self.__color_frame.setDepthTest(False)
        self.__color_frame.setDepthWrite(False)

        # 2. 中間：少し小さい白い矩形（カード背景）
        self.__white_frame = DirectFrame(
            frameColor=(1.0, 1.0, 1.0, 1.0),
            frameSize=(-0.25, 0.25, -0.1, 0.1),
            pos=(0, 0, 0),
            parent=self.__node_path
        )
        self.__white_frame.setBin("fixed", 1)
        self.__white_frame.setDepthTest(False)
        self.__white_frame.setDepthWrite(False)

        # 3. 前面：暗転用オーバーレイ（敗者を隠す半透明黒枠）
        self.__dark_overlay = DirectFrame(
            frameColor=(0, 0, 0, 0.3),
            frameSize=(-0.27, 0.27, -0.12, 0.12),
            pos=(0, 0, 0),
            parent=self.__node_path
        )
        self.__dark_overlay.setBin("fixed", 3)
        self.__dark_overlay.setTransparency(TransparencyAttrib.MAlpha)
        self.__dark_overlay.hide()

        # 4. 最前面：プレイヤー名テキスト
        self.__name = OnscreenText(
            text="",
            pos=(0, -0.035),
            scale=0.12,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            font=self.__base.resource_context.font.mplus_bold,
            parent=self.__node_path,
            sort=10
        )

        self.__node_path.setBin("fixed", 2)
        self.__node_path.setDepthTest(False)
        self.__node_path.setDepthWrite(False)

        if not is_final:
            self.select()

    def select(self):
        """初期設定（1回戦用）"""
        setting = marble_graphics_setting_list[self.__index]
        self.__name.setText(setting.name)
        self.__color = setting.color_mid.float_rgb + (1,)
        
        # 色の矩形にプレイヤーカラーを適用
        self.__color_frame["frameColor"] = self.__color
        # 白背景の上の文字色（プレイヤーカラー適用）
        self.__name["fg"] = self.__color

    def copy_from(self, source_ui: 'TournamentPlayerUI'):
        """他のUI枠から名前とカラー情報をコピーして表示（勝ち上がり時）"""
        self.__name.setText(source_ui.__name.getText())
        self.__color = source_ui.__color
        
        # コピー元のカラーを適用
        self.__color_frame["frameColor"] = self.__color
        self.__name["fg"] = self.__color

    def set_dark(self, is_dark: bool):
        """敗者を暗く表示"""
        if is_dark:
            self.__dark_overlay.show()
        else:
            self.__dark_overlay.hide()

    def start_highlight(self):
        """次の対戦カードとしてフレームを拡大・縮小点滅させるアニメーション"""
        self.stop_highlight()
        self.__anim = Sequence(
            LerpScaleInterval(self.__node_path, 0.4, scale=1.15, startScale=1.0),
            LerpScaleInterval(self.__node_path, 0.4, scale=1.0, startScale=1.15)
        )
        self.__anim.loop()

    def stop_highlight(self):
        """アニメーション停止"""
        if self.__anim:
            self.__anim.finish()
            self.__anim = None
        self.__node_path.setScale(1.0)



class Confetti:
    """紙吹雪パーティクル生成マネージャ。"""

    def __init__(self, base, winner_index: int) -> None:
        self.__base = base
        self.__winner_index = winner_index
        self.__is_active = False
        self.__spawn_timer = 0.0
        self.__spawn_interval = 0.08  # 1秒間に約12〜15個生成

    def start(self) -> None:
        """紙吹雪の生成を開始"""
        self.__is_active = True

    def stop(self) -> None:
        """紙吹雪の生成を停止"""
        self.__is_active = False

    def update(self) -> None:
        """毎フレーム呼び出して紙吹雪を生成"""
        if not self.__is_active:
            return

        dt = globalClock.getDt()
        self.__spawn_timer += dt

        while self.__spawn_timer >= self.__spawn_interval:
            self.__spawn_timer -= self.__spawn_interval
            ParticleConfetti(self.__base, self.__winner_index)


class ParticleConfetti:
    """舞い落ちる紙吹雪パーティクル。"""

    def __init__(self, base, winner_index: int) -> None:
        self.__base = base

        # 優勝者のカラーを基本にしつつ、たまに金/銀/白を混ぜて華やかにする
        if random.random() < 0.3:
            # 金・白などのアクセントカラー
            color = random.choice([
                (1.0, 0.84, 0.0),  # 金
                (1.0, 1.0, 1.0),   # 白
                (0.9, 0.9, 0.98)   # 銀
            ])
        else:
            # 優勝プレイヤーの色
            player_setting = marble_graphics_setting_list[winner_index]
            color = player_setting.color_mid.float_rgb

        self.__node_path = base.aspect2d.attachNewNode("ParticleConfetti")
        
        # 1.0より手前（前面）に描画
        DirectFrame(
            frameColor=color + (1.0,),
            frameSize=(-0.025, 0.025, -0.025, 0.025),
            pos=(0, 0, 0),
            parent=self.__node_path,
        )
        self.__node_path.setBin("fixed", 200)
        self.__node_path.setDepthTest(False)
        self.__node_path.setDepthWrite(False)

        # 動きのパラメータをランダム設定
        self.__fall_speed = random.uniform(0.6, 1.2)
        self.__swing_amplitude = random.uniform(0.05, 0.25)
        self.__swing_speed = random.uniform(2.0, 6.0)
        self.__rotate_speed = random.uniform(90.0, 360.0)

        # 画面上部のランダムな位置から生成
        self.__start_x = random.uniform(-1.7, 1.7)
        self.__node_path.setPos(self.__start_x, 0, 1.1)

        self.__task_name = f"confetti_{id(self)}"
        self.__base.taskMgr.add(self.__update, self.__task_name)

    def __update(self, task) -> int:
        dt = globalClock.getDt()
        t = task.time

        pos = self.__node_path.getPos()
        pos.z -= self.__fall_speed * dt
        pos.x = self.__start_x + math.sin(t * self.__swing_speed) * self.__swing_amplitude
        self.__node_path.setPos(pos)

        # ひらひら舞い散る回転
        h, p, r = self.__node_path.getHpr()
        h += self.__rotate_speed * dt
        r += self.__rotate_speed * 0.7 * dt
        self.__node_path.setHpr(h, p, r)

        # 画面下に消えたら削除
        if pos.z < -1.1:
            self.__node_path.removeNode()
            return Task.done

        return Task.cont
