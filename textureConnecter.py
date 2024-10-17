import maya.cmds as cmds
from PySide2 import QtWidgets,QtGui,QtCore
from maya.app.general import mayaMixin
import re
import subprocess
import pathlib
import itertools

#  エラー用ダイアログ
class ErrorWindow(mayaMixin.MayaQWidgetBaseMixin,QtWidgets.QWidget):
    def __init__(self,eText,nodeName,fullPath):
        super().__init__()
        self.msgBox = QtWidgets.QMessageBox()
        self.msgBox.setWindowTitle(self.tr("Error"))
        self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        
        messages = [self.tr('Plese select a Material'),nodeName+self.tr(' file not found.\nPlease check file path.\n')+'"'+fullPath+'"',self.tr('The image file and material name do not match.\nPlease make sure you have selected the correct material.')]

        self.msgBox.setText(messages[eText])
        self.ok = self.msgBox.addButton(QtWidgets.QMessageBox.Ok)
        self.clip = None

    def toClipBoard(self,path):
        self.path = path
        self.clip = self.msgBox.addButton(self.tr('Copy to clipboard'),QtWidgets.QMessageBox.ActionRole)
        
    def openWindow(self):
        self.msgBox.exec()
        if self.msgBox.clickedButton() == self.clip:
            subprocess.run("clip", input=self.path, text=True)
        closeOldWindow("Error")

#  ウィンドウの見た目と各機能
class MainWindow(mayaMixin.MayaQWidgetBaseMixin,QtWidgets.QWidget):
    def __init__(self,title,translator):
        super().__init__()
        
        self.translator = translator
        self.save=True

        load = loadvar()  # 前回の変数呼び出し
        try:
            ch1,ch2,ch3,ch4,ch5,ch6,ch7 = load[0]
        except TypeError:
            ch1,ch2,ch3,ch4,ch5,ch6,ch7 = [0,0,0,0,0,0,0]
            
        texpath = load[1]

        self.setWindowTitle(title)
        Mainlayout = QtWidgets.QVBoxLayout()

        #  言語選択
        layout2 = QtWidgets.QHBoxLayout()
        self.combobox1 = QtWidgets.QComboBox(self)
        self.combobox1.addItems(["日本語", "English"])
        self.combobox1.setCurrentIndex(load[2])
        self.combobox1.currentIndexChanged.connect(self.langSwitch)
        layout2.addWidget(self.combobox1)
        #  リセットボタン
        self.button1 = QtWidgets.QPushButton(self.tr("reset"))
        self.button1.clicked.connect(self.pushed_button1)
        layout2.addWidget(self.button1)
        Mainlayout.addLayout(layout2)
       #  マテリアル選択
        self.combobox2 = QtWidgets.QComboBox(self)
        self.combobox2.addItems(["StandardSurface & aiStandardSurface", "RedShiftMaterial", "RedShiftStandardMaterial"])
        self.combobox2.setCurrentIndex(load[3])
        Mainlayout.addWidget(self.combobox2)
        #  テクスチャ選択
        layout3 = QtWidgets.QHBoxLayout()
        self.checkbox1 = QtWidgets.QCheckBox("BaseColor")
        self.checkbox1.setChecked(ch1)
        self.checkbox1.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox1)
        self.checkbox2 = QtWidgets.QCheckBox("Metalness")
        self.checkbox2.setChecked(ch2)
        self.checkbox2.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox2)
        self.checkbox3 = QtWidgets.QCheckBox("Roughness")
        self.checkbox3.setChecked(ch3)
        self.checkbox3.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox3)
        Mainlayout.addLayout(layout3)

        layout4 = QtWidgets.QHBoxLayout()
        self.checkbox4 = QtWidgets.QCheckBox("Normal")
        self.checkbox4.setChecked(ch4)
        self.checkbox4.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox4)
        self.checkbox5 = QtWidgets.QCheckBox("Height")
        self.checkbox5.setChecked(ch5)
        self.checkbox5.stateChanged.connect(self.scaleVisible)
        self.checkbox5.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox5)
        self.checkbox6 = QtWidgets.QCheckBox("Emissive")
        self.checkbox6.setChecked(ch6)
        self.checkbox6.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox6)
        self.checkbox7 = QtWidgets.QCheckBox("Opacity")
        self.checkbox7.setChecked(ch7)
        self.checkbox7.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox7)
        Mainlayout.addLayout(layout4)
        #  Heightスケール
        layout5 = QtWidgets.QHBoxLayout()
        self.textbox = QtWidgets.QLabel("Scale")
        self.textbox.setVisible(False)
        layout5.addWidget(self.textbox)
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.doubleSpinBox.setRange(0, 1)
        self.doubleSpinBox.setValue(load[4])
        self.doubleSpinBox.valueChanged.connect(self.setSliderV)
        self.doubleSpinBox.setSingleStep(0.1) 
        self.doubleSpinBox.setVisible(False)
        layout5.addWidget(self.doubleSpinBox)
        self.slider = QtWidgets.QSlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(self.setDSBV)
        self.slider.setVisible(False)
        layout5.addWidget(self.slider)
        Mainlayout.addLayout(layout5)
        #  テクスチャパス
        layout6 = QtWidgets.QHBoxLayout()
        self.textbox2 = QtWidgets.QLineEdit("Texture Path")
        self.textbox2.setText(texpath)
        layout6.addWidget(self.textbox2)
        self.button2 = QtWidgets.QPushButton("...")
        self.button2.clicked.connect(self.pushed_button2)
        layout6.addWidget(self.button2)
        Mainlayout.addLayout(layout6)
        #  実行ボタン
        layout7 = QtWidgets.QHBoxLayout()
        self.button3 = QtWidgets.QPushButton(self.tr("Connect"))
        self.button3.clicked.connect(self.pushed_button3)
        layout7.addWidget(self.button3)
        self.button4 = QtWidgets.QPushButton(self.tr("Close"))
        self.button4.clicked.connect(self.pushed_button4)
        layout7.addWidget(self.button4)
        Mainlayout.addLayout(layout7)

        self.setLayout(Mainlayout)
        
        self.disableButton()
        if ch5 == 1:
            self.scaleVisible(True)
    
    def langSwitch(self):
        if self.combobox1.currentIndex() == 0:
            qm_file = r"texCon_Jp.qm"
        else:
            qm_file = r"texCon_En.qm"
        
        self.translator.load(qm_file,directory=pm.workspace(q=True,rootDirectory=True)+'\\scripts\\i18n')
        QtCore.QCoreApplication.installTranslator(self.translator)
        self.button1.setText(self.tr("reset"))
        self.button3.setText(self.tr("Connect"))
        self.button4.setText(self.tr("Close"))
        
    #  リセット
    def pushed_button1(self):
        resetvariable(self)
    #  ファイル選択
    def pushed_button2(self):
        basepath = pathlib.Path(cmds.workspace(q=True,rootDirectory=True)+'\\sourceimages\\texture')
        if basepath.exists()==False:
            basepath = pathlib.Path(cmds.workspace(q=True,rootDirectory=True)+'\\sourceimages')
        chpath = QtWidgets.QFileDialog.getExistingDirectory()
        print(chpath)
        if(chpath==None):
            return
        path2= re.sub('.*sourceimages','sourceimages',chpath)
        self.textbox2.setText(path2)
    
    #  実行
    def pushed_button3(self):
        namereplace(self)    
    #  閉じる
    def pushed_button4(self):
        self.close()
    #  ボックスからスライダーに
    def setSliderV(self):
        value = self.doubleSpinBox.value()*100
        self.slider.setValue(value)
    #  スライダーからボックスに
    def setDSBV(self):
        value = self.slider.value()*0.01
        self.doubleSpinBox.setValue(value)
    #  スケールの表示非表示
    def scaleVisible(self,bool):
        if bool:
            self.textbox.setVisible(True)
            self.doubleSpinBox.setVisible(True)
            self.slider.setVisible(True)
        else:
            self.textbox.setVisible(False)
            self.doubleSpinBox.setVisible(False)
            self.slider.setVisible(False)
    #  実行ボタンの表示変更
    def disableButton(self):
        if not self.checkbox1.isChecked() and not self.checkbox2.isChecked() and not self.checkbox3.isChecked() and not self.checkbox4.isChecked() and not self.checkbox5.isChecked() and not self.checkbox6.isChecked() and not self.checkbox7.isChecked():
            self.button3.setEnabled(False)
        else:
            self.button3.setEnabled(True)
    #  終了時の処理
    def closeEvent(self, event):
        savevar(self)

# 接続
def baseColor(f,files,input,imgPath):  # ベースカラー
    cmds.connectAttr((files+'.outColor'),input,f=True)
    cmds.setAttr((files+'.fileTextureName'),imgPath,type='string')  # Fileノードに画像を設定

def normal(f,files,input,imgPath,rs,p2t):
    if rs==0:
        normal = cmds.shadingNode('aiNormalMap', asUtility=True)  # aiノーマルマップ作成
        cmds.connectAttr(normal+'.outValue',input,f=True)
    else:
        cmds.delete(files)
        cmds.delete(p2t)
        normal = cmds.shadingNode('RedshiftNormalMap', asUtility=True)  # rsノーマルマップ作成
        cmds.connectAttr(normal+'.outDisplacementVector',input,f=True)
        cmd.setAttr(normal+'.tex0.set',imgPath,type='string')
        return()
    cmds.setAttr(files+'.ignoreColorSpaceFileRules',1)  # カラースペース変更、変更を固定
    cmds.setAttr(files+'.cs',"Raw",type='string')
    cmds.setAttr(files+'.alphaIsLuminance',1)  # アルファ値に輝度を使用
    cmds.connectAttr(files+'.outColor',normal+'.input',f=True)
    cmds.setAttr(files+'.fileTextureName',imgPath,type='string')  # Fileノードに画像を設定

def height(f,files,input,inputSG,imgPath,rs,hScale):
    cmds.setAttr(files+'.ignoreColorSpaceFileRules',1)  # カラースペース変更、変更を固定
    cmds.setAttr(files+'.cs',"Raw",type='string')
    cmds.setAttr(files+'.alphaIsLuminance',1)  # アルファ値に輝度を使用
    if rs==0:
        disp = cmds.shadingNode('displacementShader', asUtility=True)  # Heightマップ用のディスプレイスメントを作成
        cmds.connectAttr(files+'.outAlpha',disp+'.displacement',f=True)
        for i in range(len(inputSG)):
            cmds.connectAttr(disp+'.displacement',inputSG[i]+'.displacementShader',f=True)
    else:
        disp = cmds.shadingNode('RedshiftDisplacement', asUtility=True)
        cmds.connectAttr(files+'.outColor',disp+'.texMap',f=True)
        for i in range(len(inputSG)):
            cmds.connectAttr(disp+'.out',inputSG[i]+'.displacementShader',f=True)
    cmds.setAttr(disp+'.scale',hScale)
    cmds.setAttr(files+'.fileTextureName',imgPath,type='string')  # Fileノードに画像を設定

def othertex(f,files,input,imgPath):
    cmds.setAttr(files+'.ignoreColorSpaceFileRules',1)  # カラースペース変更、変更を固定
    cmds.setAttr(files+'.cs',"Raw",type='string')
    cmds.setAttr(files+'.alphaIsLuminance',1)  # アルファ値に輝度を使用
    cmds.connectAttr(files+'.outAlpha',input,f=True)
    cmds.setAttr(files+'.fileTextureName',imgPath,type='string')  # Fileノードに画像を設定

# 画像の分類
def Sorttex(f,files,input,inputSG,imgPath,rs,p2t,hScale):
    if(f in ['Base','Color','Opacity']):    
        baseColor(f,files,input,imgPath)
        return
    if(f == 'Normal'):    
        normal(f,files,input,imgPath,rs,p2t)
        return
    if(f in ['Height','Displace']):    
        height(f,files,input,inputSG,imgPath,rs,hScale)
        return
    if(f in ['Emissive','Metal','Roughness']):  
        othertex(f,files,input,imgPath)

# ノード作成
def nodecrate(s,i,nodeName):
    files = cmds.shadingNode('file', asTexture=True,isColorManaged=True)  # Fileノード作成
    p2t = cmds.shadingNode('place2dTexture', asUtility=True)  # P2Tノード作成
    cmds.defaultNavigation(connectToExisting=True, source=p2t, destination=files, f=True)  # 上記のノード接続
    input = s[0]+'.'+nodeName[i]  # マテリアルのアトリビュートノード名
    inputSG = cmds.listConnections(s[0],s=False,t='shadingEngine')  # シェーディングエンジンのアトリビュートノード名（Height用）
    return(files,input,inputSG,p2t)

# パスの確認
def checkPath(nodeName,fullPath,s):
    path = pathlib.Path(fullPath)
    t = path.stem
    t = t.split('_')
    for i in range(len(t)):  # 画像名のファイルがあるかチェック
        l=list(itertools.combinations(t, i))
        for j in l:
            if s[0] == str('_'.join(j)):
                return(True)
    return(False)

# テクスチャフォルダパスの調整
def projpath(nodeName,fileName,texPath,s,f):
    project = cmds.workspace(q=True,fn=True)  # パスの調整
    project = str(project.replace('/','\\')+'\\')
    n = (project+texPath)
    n = str(n.replace('/','\\'))
    p = pathlib.Path(n)
    rex = '*'+fileName+'*'
    fullPath = []
    for i in list(p.glob(rex)):
        if i.suffix in '.tx':
            continue
        else:
            fullPath.append(str(i))
    if fullPath == []:  # 設定されたパスに画像がなければ
        errorDialog = ErrorWindow(1,nodeName,n)
        errorDialog.toClipBoard(n)
        errorDialog.openWindow()
        return (False)
    for i in fullPath:
        ch = checkPath(nodeName,i,s)
        if ch==True:
            fullPath=i
            break
    else:
        errorDialog = ErrorWindow(2,'','')
        errorDialog.openWindow()
        return(False)
    imgPath = str(re.sub('.*sourceimages','sourceimages',fullPath))
    return(fullPath,imgPath)

# 本体
def texplace(nodeName,fileName,texPath,rs,hScale):
    s = cmds.ls(sl=True)
    for i,f in enumerate(fileName):
        if s == []:
            errorDialog = ErrorWindow(0,'','')
            errorDialog.openWindow()
            
            break
        path = projpath(nodeName[i],fileName[i],texPath,s,f)
        if path==False:
            break
        nodes = nodecrate(s,i,nodeName)
        Sorttex(f,nodes[0],nodes[1],nodes[2],path[1],rs,nodes[3],hScale)

#マテリアルごとのノード、ファイル名
def materialNodeNames(v):
    if v==0:
        #ss&aiss
        names1 = ['baseColor','metalness','specularRoughness','normalCamera','displacementShader','emission','opacity']
        names2 = ['Base','Metal','Roughness','Normal','Height','Emissive','Opacity']
    elif v==1:
        #rsm
        names1 = ['diffuse_color','metalness','refl_roughness','bump_input','displacementShader','emission_color','opacity_color']
        names2 = ['Color','Metal','Roughness','Normal','Displace','Emissive','Opacity']
    elif v==2:
        #rssm
        names1 = ['base_color','metalness','refl_roughness','bump_input','displacementShader','emission_color','opacity_color']
        names2 = ['Color','Metal','Roughness','Normal','Displace','Emissive','Opacity']
    return([names1,names2])

# ノード接続用の名前変更
def namereplace(self):
    names = materialNodeNames(self.combobox2.currentIndex())
    nodeName=[]
    fileName=[]
    chlist=[]
    chlist.append(int(self.checkbox1.isChecked()))
    chlist.append(int(self.checkbox2.isChecked()))
    chlist.append(int(self.checkbox3.isChecked()))
    chlist.append(int(self.checkbox4.isChecked()))
    chlist.append(int(self.checkbox5.isChecked()))
    chlist.append(int(self.checkbox6.isChecked()))
    chlist.append(int(self.checkbox7.isChecked()))
    for i, ch in enumerate(chlist):
        checks = 'check'+str(i+1)  # チェックが入っているものだけリストにする
        if ch == 1:
            nodeName.append(names[0][i])
            fileName.append(names[1][i])
    texPath = self.textbox2.text()
    rs = self.combobox2.currentIndex()
    hScale = self.doubleSpinBox.value()
    texplace(nodeName,fileName,texPath,rs,hScale)

# エラー時メッセージ
def errorlanguage(nodeName,fullPath):
    en = ['Plese select a Material',nodeName+' file not found.\nPlease check file path.\n'+'"'+fullPath+'"','The image file and material name do not match.\nPlease make sure you have selected the correct material.','Copy to clipboard','Close']
    jp = ['マテリアルを選択してください。',nodeName+' ファイルが見つかりません。\n以下のフォルダに画像があるかを確認してください。\n'+'"'+fullPath+'"','画像ファイルとマテリアル名が一致しません。\n正しいマテリアルを選択しているか確認してください。','クリップボードにコピー','閉じる']
    return jp

# 変数の記憶
def savevar(self):
    chlist = [0,0,0,0,0,0,0]
    cmds.optionVar(ia='checklist')
    chlist[0] = int(self.checkbox1.isChecked())
    chlist[1] = int(self.checkbox2.isChecked())
    chlist[2] = int(self.checkbox3.isChecked())
    chlist[3] = int(self.checkbox4.isChecked())
    chlist[4] = int(self.checkbox5.isChecked())
    chlist[5] = int(self.checkbox6.isChecked())
    chlist[6] = int(self.checkbox7.isChecked())
    for i in range(7):
        cmds.optionVar(iva=['checklist',chlist[i]])  # データをuserPrefs.melに保存

    if self.textbox2.text() != 'sourceimages/texture/':  # テクスチャフォルダパスの保存
        cmds.optionVar(sv=['texPath',self.textbox2.text()])  # データをuserPrefs.melに保存
    
    lan = int(self.combobox1.currentIndex())  # 言語設定
    cmds.optionVar(iv=['texlanguage',lan])  # データをuserPrefs.melに保存
    
    mat = int(self.combobox2.currentIndex())  # マテリアル設定
    cmds.optionVar(iv=['texmaterials',mat])  # データをuserPrefs.melに保存
    
    scl = self.doubleSpinBox.value()  # ハイトのスケール
    cmds.optionVar(fv=['texhScale',scl])  # データをuserPrefs.melに保存

# 変数の呼び出し
def loadvar():
    if (cmds.optionVar(ex='checklist')==True):  # 前回の設定読み込みまたは新規で作成
        chlist = cmds.optionVar(q='checklist')
    else:
        chlist = [0,0,0,0,0,0,0]
    if (cmds.optionVar(ex='texPath')==True):
        texpath = cmds.optionVar(q='texPath')
    else:
        texpath = 'sourceimages\\texture\\'
    if (cmds.optionVar(ex='texlanguage')==True):
        lan = cmds.optionVar(q='texlanguage')
    else:
        lan = 1
    if (cmds.optionVar(ex='texmaterials')==True):
        mat = cmds.optionVar(q='texmaterials')
    else:
        mat = 1
    if (cmds.optionVar(ex='texhScale')==True):
        hScale = cmds.optionVar(q='texhScale')
    else:
        hScale = 0.5
    return [chlist,texpath,lan,mat,hScale]

# 入力リセット
def resetvariable(self):
    cmds.optionVar(ia=['checklist'])
    cmds.optionVar(sv=['texPath','sourceimages\\texture\\'])
    cmds.optionVar(iv=['texlanguage',1])
    cmds.optionVar(iv=['texmaterials',1])
    cmds.optionVar(fv=['texhScale',0.5])
    
    self.checkbox1.setChecked(False)
    self.checkbox2.setChecked(False)
    self.checkbox3.setChecked(False)
    self.checkbox4.setChecked(False)
    self.checkbox5.setChecked(False)
    self.checkbox6.setChecked(False)
    self.checkbox7.setChecked(False)
    self.textbox2.setText('sourceimages\\texture\\')

    self.combobox2.setCurrentIndex(0)
    self.doubleSpinBox.setValue(0.5)

#  ウィンドウがすでに起動していれば閉じる
def closeOldWindow(title):
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if title == widget.windowTitle():
           widget.deleteLater()
           widget.close()

#  アプリの実行と終了
def openWindow():
    
    title = "Texture_Connect"
    closeOldWindow(title)
    app = QtWidgets.QApplication.instance()
    if cmds.optionVar(q='texlanguage') == 0:
        qm_file = r"texCon_Jp.qm"
    else:
        qm_file = r"texCon_En.qm"
    
    translator = QtCore.QTranslator(app)
    translator.load(qm_file,directory = pm.workspace(q=True,rootDirectory=True)+'\\scripts\\i18n')
    QtCore.QCoreApplication.installTranslator(translator)
    
    window = MainWindow(title,translator)
    window.show()
    app.exec_()
    
if __name__ == "__main__":
    openWindow()
