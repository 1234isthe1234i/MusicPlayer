from __future__ import annotations
import random, os, sys
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtCore import QUrl, Qt, QTimer
from PySide6.QtGui import QIcon, QGradient, QMouseEvent, QPainter, QFontDatabase, QAction, QPixmap, QPaintEvent
from PySide6.QtWidgets import (QMainWindow, QFrame, QApplication, QLabel, QToolButton, QSlider,
                            QComboBox, QMenu, QMenuBar, QScrollArea,
                            QGraphicsDropShadowEffect, QCheckBox, QSystemTrayIcon, QWidget)


PREF_FILE = 'assets\\preset_preference.txt'

class Song:
    '''
    # Song 
    #### Holds all the information: files' paths, and QUrl for the song
    ---
    ## Parameters 
    - name [str]: The name of the song; is used to access all the various files, paths, & QUrl
    '''
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.band: str = name # Will have a differnce between song name and band in VERSION 2
        self.img: str = f'thumbnails\\{name}.jpg'
        self.path: str = f'songs\\{name}.mp3'
        self.url: QUrl = QUrl.fromLocalFile(self.path)

        if not os.path.exists(self.img):
            self.img = None


    def __repr__(self): return str(self)
    def __str__(self): return f'{self.band}'


class Window(QMainWindow):
    '''
    # Window
    #### Initializes the window, sets its attributes, and handles the widget to be displayed.
    '''
    def __init__(self):
        super().__init__()
        QFontDatabase.addApplicationFont('assets\\Space_Grotesk\\static\\SpaceGrotesk-Regular.ttf')
        self.setGeometry(width//2 - 600, height//2 - 300, 1200, 600)
        self.setWindowTitle('PulsePlay Music Player')
        self.setWindowIcon(QIcon('assets\\logo.ico'))

        self.audio_init()

        self.preset: str | QGradient.Preset = ''

        self.load_attr()

    def load_attr(self):
        '''
        load_attr
        ---
        Creates all the elements of the window which are static and calls the central widget handler
        '''
        menu_bar = QMenuBar(self)

        file_menu = QMenu('File', self)
        for func in ['Open', 'Save', 'Close', 'Open Multiple Files', 'Open Playlist']:
            acc = QAction(f'{func}', self)
            acc.triggered.connect(getattr(self, f'{func}'.lower().replace(' ', '_')))
            file_menu.addAction(acc)

        preset_menu = QMenu("Preset", self)
        for func in ['Save As Default', 'Change Preset']:
            acc = QAction(f'{func}', self)
            acc.triggered.connect(getattr(self, f'{func}'.lower().replace(' ', '_')))
            preset_menu.addAction(acc)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(preset_menu)

        self.setMenuBar(menu_bar)

        self.tray = QSystemTrayIcon(QIcon('assets\\logo.ico'), self)
        menu = QMenu(self)
        for index, (name, func) in enumerate([['Quit', sys.exit], ['Show Window', self.show], ['Quit on Close', lambda: app.setQuitOnLastWindowClosed(not app.quitOnLastWindowClosed())]]):
            a = QAction(name, self)
            if index == 2: 
                a.setCheckable(True) 
                a.setChecked(True)
            a.triggered.connect(func)
            menu.addAction(a)
        self.tray.setContextMenu(menu)
        self.tray.setVisible(True)

        self.c_widget_handler()

    def c_widget_handler(self):
        '''
        c_widget_handler
        ---
        Checks if a default preset is configured by the user and displays the main widget. Else, displays a widget which allows the user to pick a preset
        '''
        with open(PREF_FILE, 'r') as f:
            read = f.read()
            if len(read) == 0:
                self.scroll_area = QScrollArea()
                self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
                self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.scroll_area.setWidget(Show_Presets(self))
                self.setCentralWidget(self.scroll_area)
            else:
                self.setCentralWidget(Home_Page(self, getattr(QGradient.Preset, read)))

    # The Following functions are not implemented yet, and will be added later. 

    def open(self): raise NotImplementedError("WILL WORK IN VERSION 2")
    def save(self): raise NotImplementedError("WILL WORK IN VERSION 2")
    def close(self): raise NotImplementedError("WILL WORK IN VERSION 2")
    def open_multiple_files(self): raise NotImplementedError("WILL WORK IN VERSION 2")
    def open_playlist(self): raise NotImplementedError("WILL WORK IN VERSION 2")

    def save_as_default(self):
        '''
        save_as_default
        ---
        This function sets the current preset as the default, so that the program will automatically load this on startup.
        '''
        with open(PREF_FILE, 'a+') as pref:
            pref.truncate()
            pref.write(self.preset.name)

    def change_preset(self):
        '''
        change_preset
        ---
        This function removes the current default preset and allows the user to pick another preset
        '''
        with open(PREF_FILE, 'w+') as pref: pref.truncate()
        
        self.preset = ''
        self.c_widget_handler()

        self.player.pause()

    def audio_init(self):
        '''
        audio_init
        ---
        This function creates the instances which allow for the music to be played. 
        '''
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(100)


class Show_Presets(QWidget):
    '''
    # Show_Presets
    #### Shows all the presets and their preview, so that the user can pick the prefered preset.
    ---
    ## Parameters
    - win [Window]: The Window instance which holds all the static elements of the window.
    '''
    def __init__(self, win: Window):
        super().__init__(win)
        self.setGeometry(0, 0, 1180, len(list(QGradient.Preset.__members__.values()))//((win.width()-100)//240)*260+50)
        x, y = 100, 50
        for preset in list(QGradient.Preset.__members__.values())[:-1]:
            Preset_Preview(self, getattr(QGradient.Preset, preset.name), x, y, win)
            x += 260
            if x + 240 > self.width():
                x = 100
                y += 260


class Preset_Preview(QFrame):
    '''
    # Preset_Preview
    #### Creates one preset preview
    --- 
    ## Parameters
    - sh_p [Show_Presets]: The Show_Presets instance which the Preset Preview will be displayed on.
    - preset [QGradient.Preset]: The QGradient Preset that this Preset Preview will show.
    - x_pos [int]: The X-Pos of this preview on the screen.
    - y_pos [int]: The Y-Pos of this preview on the screen.
    - win [Window]: The Window instance which is used to set the selected preset onto the window.
    '''
    def __init__(self, sh_p: Show_Presets, preset: QGradient.Preset, x_pos: int, y_pos: int, win: Window):
        super().__init__(sh_p)
        self.win = win
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0)

        self.setGeometry(x_pos, y_pos, 200, 200)
        self.setStyleSheet('background-color: white; border-radius: 5px; border: 1px solid black;')
        self.setGraphicsEffect(shadow)

        self.preset = preset

        self.load_attr()

    def load_attr(self):
        '''
        load_attr
        ---
        Creates the label of the name of the preset
        '''
        lbl = QLabel(f'{self.preset.name} {self.preset.value}', self)
        lbl.setGeometry(1, 1, self.width()-2, 22)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet('border: none; font-size: 20px; font-family: Space Grotesk;')

    def paintEvent(self, event: QPaintEvent):
        '''
        paintEvent
        ---
        Creates a small preview of the preset
        '''
        p = QPainter(self)
        p.setBrush(QGradient(self.preset))
        p.drawEllipse(self.width()/4, self.height()/4 + 10, self.width()/2, self.height()/2)
        return super().paintEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''
        mousePressEvent
        ---
        Sets the selected preview to the window
        '''
        home_pg = Home_Page(self.win, self.preset)
        window.setCentralWidget(home_pg)
        home_pg.controls.update_song_info()
        return super().mousePressEvent(event)


class Home_Page(QFrame):
    '''
    # Home_Page
    #### The Base which the Preset is applied to, and which stoes the controls of the music player. 
    ---
    ## Parameters
    - win [Window]: the Window object which holds all attributes of the window
    - preset [QGradient.Preset]: the Preset that was selected by the user and applied to the Home_Page
    '''
    def __init__(self, win: Window, preset: QGradient.Preset):
        super().__init__(win)
        self.parent_win = win
        self.preset = QGradient(preset)
        win.preset = preset
        self.setGeometry(0,0, win.width(), win.height())
        self.song_info = Song_Info(self)
        self.controls = Controls(self, win.audio_output, win.player, (self.preset.stops()[0][1].toTuple(), self.preset.stops()[-1][1].toTuple()))

    def paintEvent(self, event) -> None:
        '''
        paintEvent
        ---
        paints the supplied preview to the Home_Page
        '''
        painter = QPainter(self)
        painter.setBrush(self.preset)
        painter.drawRect(0, 0, self.parent_win.width(), self.parent_win.height())
        return super().paintEvent(event)

class Song_Info(QFrame):
    '''
    # Song_Info
    #### This class holds the elements which display the album information
    ---
    ## Parameters
    - home [Home_Page]: the Home page isntance
    '''
    def __init__(self, home: Home_Page) -> None:
        super().__init__(home)
        self.setStyleSheet('background-color: transparent;')
        self.setGeometry(50, 275, 700, 200)
        self.load_attr()

    def load_attr(self):
        '''
        load_attr
        ---
        loads the attributes which will display the song ifo
        '''
        self.art = QLabel(self)
        self.art.setGeometry(0,0, 200, 150)
        self.art.setStyleSheet('background-color: #242424;')
        
        self.title = QLabel(self)
        self.title.setGeometry(225, 30, 475, 40)
        self.title.setStyleSheet('font-size: 20px; font-family: Space Grotesk;')
        self.title.setWordWrap(True)
        
        self.band_name = QLabel(self)
        self.band_name.setGeometry(225, 80, 475, 30)
        self.band_name.setStyleSheet('font-size: 15px; font-family: Space Grotesk;')
        self.band_name.setWordWrap(True)

class Controls(QFrame):
    '''
    # Controls
    #### Houses all the buttons and sliders of the control "panel"
    ---
    ## Parameters
    - home [Home_Page]: The home page instance 
    - audio_output [QAudioOutput]: the QAudioOutput instance which configures the speakers
    - player [QMediaPlayer]: the QMediaPlayer instance which is used to set the song
    - preset [tuple[tuple[int]]]: the color preset used as a tuple of rgba values
    '''
    def __init__(self, home: Home_Page, audio_output: QAudioOutput, player: QMediaPlayer, preset: tuple[tuple[int]]):
        super().__init__(home)
        self.setGeometry(0, 450, 1200, 100)

        self.audio_output = audio_output
        self.player = player
        self.colors = preset
        self.home = home
        self.song_info = home.song_info

        self.song_num = 1

        self.shuffled = False
        self.first = True
        self.humanInterventionOnSong = False

        self.songs: dict[int, Song] = {index+1: Song(song[:-4]) for index, song in enumerate(os.listdir('songs'))}
        self.curr_song = self.songs.get(self.song_num)

        self.player.setSource(self.curr_song.url)        
        self.player.mediaStatusChanged.connect(self.song_end_start)

        self.rep_timer = QTimer(self)
        self.rep_timer.timeout.connect(self.time_setter)
        self.rep_timer.setInterval(0)

        self.load_attr()
        self.stop()
        

    def load_attr(self):
        '''
        load_attr
        ---
        loads all the controls and configures them
        '''
        self.song_pos = QSlider(self)
        self.song_pos.setGeometry(100, 0, 1000, 20)
        self.song_pos.setSliderPosition(0)
        self.song_pos.setOrientation(Qt.Orientation.Horizontal)
        self.song_pos.sliderMoved.connect(self.change_song_pos)

        for i, button in enumerate(['previous_song', 'rewind', 'play', 'stop', 'seek', 'next_song', 'shuffle']):
            b = QToolButton(self)
            b.setGeometry(50+i*30, 50, 25, 25)
            b.setIcon(QIcon(f'assets\\{button}.png'))
            b.setStyleSheet(f'QToolButton {{background-color: rgba{self.colors[0]};}} QToolButton::hover {{background-color: rgba{self.colors[1]};}}')
            b.clicked.connect(getattr(self, button))
            self.__setattr__(f"{button}_button", b)
        
        self.autoplay = QCheckBox('AutoPlay', self)
        self.autoplay.setStyleSheet(f'''
        QCheckBox {{font-size: 13px; font-family: Space Grotesk; border: 1px solid black; background-color: rgba{self.colors[0]};}}
        QCheckBox::checked {{background-color: rgba{self.colors[1]};}}''')
        self.autoplay.setGeometry(b.x() + 30, 50, 80, 25)
        self.autoplay.setChecked(True)

        self.vol = QSlider(self)
        self.vol.setGeometry(950, 25, 200, 20)
        self.vol.setRange(0, 100)
        self.vol.setSliderPosition(20)
        self.vol.setOrientation(Qt.Orientation.Horizontal)
        self.vol.sliderMoved.connect(self.change_vol)

        self.devices_list = QComboBox(self)
        self.devices_list.setGeometry(950, 50, 200, 25)
        self.devices_list.setStyleSheet(f'font-size: 10px; font-family: Space Grotesk; background-color: rgba{self.colors[0]};')
        self.devices_list.activated.connect(self.change_audio_output)
        for device in QMediaDevices.audioOutputs():
            self.devices_list.addItem(device.description())
        
        self.curr_time = QLabel('00:00', self)
        self.curr_time.setGeometry(50, 0, 45, 20)
        self.curr_time.setStyleSheet(f'font-size: 15px; font-family: Space Grotesk;')

        self.end_time = QLabel(self)
        self.end_time.setGeometry(1105, 0, 45, 20)
        self.end_time.setStyleSheet(f'font-size: 15px; font-family: Space Grotesk;')
        
    def change_audio_output(self, device: str):
        '''
        ## change_audio_output 
        ##### changes the speaker device which plays the music
        ---
        ## Parameters
        - device [str]: the name of the device which should play the music
        '''
        self.audio_output.setDevice(QMediaDevices.audioOutputs()[device])
        
    def change_vol(self, position: int):
        '''
        ## change_vol
        ##### changes the app volume 
        ---
        ## Parameters
        - position [int]: the valume that the speaker should change to
        '''
        [session for session in AudioUtilities.GetAllSessions() if session.Process and session.Process.name() == 'python.exe'][0]._ctl.QueryInterface(ISimpleAudioVolume).SetMasterVolume(position/100, None)        
    
    def shuffle(self):
        '''
        shuffle
        ---
        if the songs are already shuffled then they will be sorted alphabetically

        if the songs are not shuffled, then they are shuffled
        '''
        if not self.shuffled:
            ls = list(self.songs.values())
            random.shuffle(ls)
            self.song_num = ls.index(self.curr_song) + 1
            self.shuffled = True
            self.shuffle_button.setStyleSheet(f'QToolButton {{background-color: rgba{self.colors[1]};}} QToolButton::hover {{background-color: rgba{self.colors[0]};}}')
        elif self.shuffled:
            self.shuffled = False
            ls = sorted(list(self.songs.values()), key=lambda x: x.name)
            self.song_num = ls.index(self.curr_song) + 1
            self.shuffle_button.setStyleSheet(f'QToolButton {{background-color: rgba{self.colors[0]};}} QToolButton::hover {{background-color: rgba{self.colors[1]};}}')
        
        self.songs = {index+1: val for index, val in enumerate(ls)}
    
    def rewind(self):
        '''
        rewind
        ---
        this function rewinds the song 10 seconds
        '''
        self.player.setPosition(self.player.position()-10000)

    def seek(self):
        '''
        seek
        ---
        this function seeks the song forward 10 seconds
        '''
        self.player.setPosition(self.player.position()+10000)
    
    def stop(self):
        '''
        stop
        ---
        pauses the music and restarts the song. 
        '''
        self.player.pause()
        self.player.setPosition(0)
        self.song_pos.setSliderPosition(0)
        self.play_button.setIcon(QIcon('assets\\play.png'))

    def play(self):
        '''
        play
        ---
        this function plays the music if it is paused and pauses the music if it is playing
        '''
        self.player.pause() if self.player.isPlaying() else self.player.play()
        self.play_button.setIcon(QIcon(f"assets\\{'pause.png' if self.player.isPlaying() else 'play.png'}"))
        self.song_pos.setRange(0, self.player.duration())
        self.rep_timer.start()

    def change_song_pos(self, position: int):
        '''
        ## change_song_pos
        ##### Adjusts the playback position of the current song.
        ---
        ## Parameters:
        - position [int]: The new position in milliseconds to which the song should be set.
        '''
        self.player.setPosition(position)


    def next_song(self):
        '''
        ## next_song
        ---
        changes the current song to the next song
        '''
        self.humanInterventionOnSong = True
        self.song_num = self.song_num + 1 if self.song_num != len(self.songs) else 1
        self.player.setPosition(self.player.duration())
        if not self.player.isPlaying(): self.play()

    def previous_song(self):
        '''
        ## previous_song
        ---
        changes the current song to the previous song
        '''
        self.humanInterventionOnSong = True
        self.song_num = self.song_num - 1 if self.song_num != 1 else len(self.songs)
        self.player.setPosition(self.player.duration())
        if not self.player.isPlaying(): self.play()

    def time_setter(self):
        '''
        time_setter
        ---
        updates the time stamp according to the playback position of the song
        '''
        self.song_pos.setSliderPosition(self.player.position())
        if self.first and 0 < self.player.position() < 100:
            self.first = False
            self.seek()
            self.rewind()
        m = self.player.position()//60000
        s = round(self.player.position()/1000)%60
        self.curr_time.setText(f'{m if m >= 10 else f"0{m}"}:{s if s >= 10 else f"0{s}"}')

    def update_song_info(self):
        '''
        update_song_info
        ---
        changes the song info displayed when the song changes
        '''
        try: self.song_info.art.setPixmap(QPixmap(self.curr_song.img).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except TypeError as e: pass
        self.song_info.title.setText(self.curr_song.name)
        self.song_info.band_name.setText(self.curr_song.band)

    def song_end_start(self, status: QMediaPlayer.MediaStatus):
        '''
        ## song_end_start
        ##### this function updates all the attributes related to the end of a song
        ---
        ## Parameters
        - status [QMediaPlayer.MediaStatus]: the status of the mediaplayer based on the playback of the song
        '''
        if status == self.player.MediaStatus.EndOfMedia:
            self.rep_timer.stop()
            
            if not self.humanInterventionOnSong: 
                self.song_num = self.song_num + 1 if self.song_num != len(self.songs) else 1
            if self.humanInterventionOnSong:
                self.humanInterventionOnSong = False

            self.curr_song = self.songs.get(self.song_num)
            self.player.setSource(self.curr_song.url)
            
            self.song_pos.setSliderPosition(0)    
            
        elif status == self.player.MediaStatus.LoadedMedia:
            
            m = self.player.duration()//60000
            s = round(self.player.duration()/1000)%60

            self.end_time.setText(f'{m if m >= 10 else f"0{m}"}:{s if s >= 10 else f"0{s}"}')
            self.curr_time.setText('00:00')
            
            if self.autoplay.isChecked(): self.player.pause()
            
            self.play()

            if self.first:
                self.play_button.setIcon(QIcon('assets\\play.png'))

            self.update_song_info()
            
            window.setWindowTitle(f"{window.windowTitle().split(' -')[0]} - {self.curr_song.name.capitalize()}")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    app = QApplication(sys.argv)
    width, height = app.screens()[0].size().toTuple()
    window = Window()
    window.show()
    sys.exit(app.exec())