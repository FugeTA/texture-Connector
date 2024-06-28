import pymel.core as pm
import re
import subprocess
import pathlib

# 接続
def baseColor(f,files,input,imgPath):  # ベースカラー
        files.outColor>>input
        pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定

def normal(f,files,input,imgPath):
        normal = pm.shadingNode('aiNormalMap', asUtility=True)  # aiノーマルマップ作成
        pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
        pm.setAttr(files.cs,"Raw")
        pm.setAttr(files.alphaIsLuminance,1)  # アルファ値に輝度を使用
        files.outColor>>normal.input
        normal.outValue>>input
        pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定

def height(f,files,input,inputSG,imgPath):
        pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
        pm.setAttr(files.cs,"Raw")
        pm.setAttr(files.alphaIsLuminance,1)  # アルファ値に輝度を使用
        disp = pm.shadingNode('displacementShader', asUtility=True)  # Heightマップ用のディスプレイスメントを作成
        files.outAlpha>>disp.displacement
        disp.displacement>>inputSG
        pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定

def othertex(f,files,input,imgPath):
        pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
        pm.setAttr(files.cs,"Raw")
        pm.setAttr(files.alphaIsLuminance,1)  # アルファ値に輝度を使用
        files.outAlpha>>input
        pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定
        return

# 画像の分類
def Sorttex(f,files,input,inputSG,imgPath):
    if(f in ['Base','Opacity']):    
        baseColor(f,files,input,imgPath)
        return
    if(f == 'Normal'):    
        normal(f,files,input,imgPath)
        return
    if(f == 'Height'):    
        height(f,files,input,inputSG,imgPath)
        return
    if(f in ['Emissive','Metal','Roughness']):  
        othertex(f,files,input,imgPath)

# ノード作成
def nodecrate(s,i,nodeName):
    files = pm.shadingNode('file', asTexture=True,isColorManaged=True)  # Fileノード作成
    p2t = pm.shadingNode('place2dTexture', asUtility=True)  # P2Tノード作成
    pm.defaultNavigation(connectToExisting=True, source=p2t, destination=files, f=True)  # 上記のノード接続
    input = s[0]+'.'+nodeName[i]  # マテリアルのアトリビュートノード名
    inputSG = s[0].shadingGroups()
    inputSG = inputSG[0]+'.'+nodeName[i]  # シェーディングエンジンのアトリビュートノード名（Height用）
    return(files,input,inputSG)

# パスの確認
def checkPath(nodeName,fullPath,lan,errors):
    path = pathlib.Path(fullPath)
    if path.exists()==False or errors == 1:  # 設定されたパスに画像があるかチェック
        missfile = pm.confirmDialog(t='Error',m=errorlanguage(nodeName,lan,fullPath)[1],b=[(errorlanguage(nodeName,lan,'')[2]),(errorlanguage(nodeName,lan,'')[3])])
        if missfile == (errorlanguage(nodeName,lan,'')[2]):
            subprocess.run("clip", input=fullPath, text=True)  # WindowsのClipを使用してクリップボードにコピー
        return (False)
    return (True)

# テクスチャフォルダパスの調整
def projpath(fileName,texPath,s,f):
    errors = 0
    project = pm.workspace(q=True,fn=True)  # パスの調整
    project = str(project.replace('/','\\')+'\\')
    n = (project+texPath)
    n = str(n.replace('/','\\'))
    p = pathlib.Path(n)
    rex = '*'+s[0]+'_'+fileName+'*'
    for i in list(p.glob(rex)):
        if i.suffix in '.tx':
            continue
        else:
            fullPath = str(i)
            break
    try:
        fullPath
    except NameError:
        fullPath = n
        errors = 1
    imgPath = str(re.sub('.*sourceimages','sourceimages',fullPath))
    return(fullPath,imgPath,errors)

# 本体
def texplace(nodeName,fileName,texPath,lan):
    s = pm.ls(sl=True)
    for i,f in enumerate(fileName):
        if s == []:
            pm.confirmDialog(t='Error',m=(errorlanguage(nodeName[i],lan,'')[0]),b=(errorlanguage(nodeName[i],lan,'')[3]))
            break
        path = projpath(fileName[i],texPath,s,f)
        if checkPath(nodeName[i],path[0],lan,path[2])==False:
            break
        nodes = nodecrate(s,i,nodeName)
        Sorttex(f,nodes[0],nodes[1],nodes[2],path[1])

# 変数の記憶
def savecheck(ws):
    chlist = [0,0,0,0,0,0,0]
    for i in range(len(chlist)):  # チェックリストの保存
        chs = 'check'+str(i+1)
        chlist[i] = ws[chs].getValue()
    pm.optionVar['checklist'] = chlist  # データをuserPrefs.melに保存

def savetex(ws):
    if ws['path'].getText() != 'sourceimages/texture/':  # テクスチャフォルダパスの保存
        path = ws['path'].getText()  # データをuserPrefs.melに保存
    else:
        path = 'sourceimages\\texture\\'
    pm.optionVar['texPath'] = path  # データをuserPrefs.melに保存

def savelang(ws):
    lan = pm.optionMenu(ws['lang'],q=True,sl=True)  # 画像形式の保存
    pm.optionVar['texlanguage'] = lan  # データをuserPrefs.melに保存

# 変数の呼び出し
def loadvar():
    if (pm.optionVar(ex='checklist')==True):  # 前回の設定読み込みまたは新規で作成
        chlist = pm.optionVar['checklist']
    else:
        chlist = [0,0,0,0,0,0,0]
    if (pm.optionVar(ex='texPath')==True):
        texpath = pm.optionVar['texPath']
    else:
        texpath = 'sourceimages\\texture\\'
        
    if (pm.optionVar(ex='texlanguage')==True):
        lan = pm.optionVar['texlanguage']
    else:
        lan = 1
    return [chlist,texpath,lan]

# 入力リセット
def resetvariable(ws):
    pm.optionVar['checklist'] = [0,0,0,0,0,0,0]
    pm.optionVar['texPath'] = 'sourceimages\\texture\\'
    pm.optionVar['imgformat'] = 1
    pm.optionVar['lang'] = 1
    for i in range(6):
        chs = 'check'+str(i+1)
        ws[chs].setValue(0)
    ws['path'].setText('sourceimages\\texture\\')
    pm.optionMenu(ws['lang'],e=True,sl=1)
    winlanguage(ws)
    pm.button(ws['button2'],e=True,en=False)

# ノード接続用の名前変更
def namereplace(ws):
    names1 = ['baseColor','specular','specularRoughness','normalCamera','displacementShader','emission','opacity']
    names2 = ['Base','Metal','Roughness','Normal','Height','Emissive','Opacity']
    nodeName=[]
    fileName=[]
    for i in range(7):
        checks = 'check'+str(i+1)  # チェックが入っているものだけリストにする
        if(ws[checks].getValue()):
            nodeName.append(names1[i])
            fileName.append(names2[i])
    texPath = ws['path'].getText()
    formats = ['','png','exr','tif']
    lan = pm.optionMenu(ws['lang'],q=True,sl=True)
    texplace(nodeName,fileName,texPath,lan)

# テクスチャフォルダの名前抽出
def texPath(ws):
    path = pm.fileDialog2(fm=3,okc='Select',dir=(pm.workspace(q=True,rootDirectory=True)+'\\sourceimages\\texture'))
    path2= re.sub('.*sourceimages','sourceimages',path[0])
    ws['path'].setText(str(path2))
    savetex(ws)

# チェックボックスが押されている時のみ実行ボタンを押せる
def changeswitch(ws):
    savecheck(ws)
    for i in range(7):
        checks = 'check'+str(i+1)
        if(ws[checks].getValue()):
            ws['button2'].setEnable(1)
            break
    else:
        ws['button2'].setEnable(0)

# 言語設定
def winlanguage(ws):
    en = ['BaseColor','Metalness','Roughness','Normal','Height','Emissive','Opacity','Texture Folder','Connect','Close','Reset','Language']
    jp = ['BaseColor','Metalness','Roughness','Normal','Height','Emissive','Opacity','テクスチャフォルダ','接続','閉じる','リセット','言語']
    if (ws['lang'].getSelect())==1:
        ln = en
    else:
        ln = jp
    for i in range(7):
        chs = 'check'+str(i+1)
        ws[chs].setLabel(ln[i])
    for i in range(4):
        btn = 'button'+str(i+1)
        ws[btn].setLabel(ln[i+7])
    ws['lang'].setLabel(ln[11])
    savelang(ws)

def errorlanguage(nodeName,lan,fullPath):
    en = ['Plese select a Material',nodeName+' file not found.\nPlease select material and check file path.\n'+'"'+fullPath+'"','Copy to clipboard','Close']
    jp = ['マテリアルを選択してください。',nodeName+' ファイルが見つかりません。\n正しいマテリアルを選択しているか、または以下のフォルダに画像があるかを確認してください。\n'+'"'+fullPath+'"','クリップボードにコピー','閉じる']
    if lan==1:
        return en
    return jp

# ウィンドウ作成
def openWindow():
    load = loadvar()  # 前回の変数呼び出し
    try:
        ch1,ch2,ch3,ch4,ch5,ch6,ch7 = load[0]
    except ValueError:
        ch1,ch2,ch3,ch4,ch5,ch6,ch7 = [0,0,0,0,0,0,0]
    texpath = load[1]
    
    winname = 'Texture_Connect'  # ウィンドウの名前
    if pm.window(winname,ex=True)==True:  # すでにウィンドウがあれば閉じてから開く
        pm.deleteUI(winname)
    with pm.window(winname):  # ウィンドウの作成
        with pm.autoLayout():
            ws = {}
            with pm.horizontalLayout():
                ws['lang'] = pm.optionMenu(l='言語',cc=pm.Callback(winlanguage,ws))  # 画像形式の指定
                pm.menuItem(l="English")
                pm.menuItem(l="日本語")
                ws['button4'] = pm.button(c=pm.Callback(resetvariable,ws))  # リセット
            with pm.horizontalLayout():
                ws['check1'] = pm.checkBox(v=ch1,cc=pm.Callback(changeswitch,ws))  # 接続したい画像の指定
                ws['check2'] = pm.checkBox(v=ch2,cc=pm.Callback(changeswitch,ws))
                ws['check3'] = pm.checkBox(v=ch3,cc=pm.Callback(changeswitch,ws))
            with pm.horizontalLayout():
                ws['check4'] = pm.checkBox(v=ch4,cc=pm.Callback(changeswitch,ws))
                ws['check5'] = pm.checkBox(v=ch5,cc=pm.Callback(changeswitch,ws))
                ws['check6'] = pm.checkBox(v=ch6,cc=pm.Callback(changeswitch,ws))
                ws['check7'] = pm.checkBox(v=ch7,cc=pm.Callback(changeswitch,ws))
                
            with pm.horizontalLayout():
                ws['path'] = pm.textField(text=texpath,cc=pm.Callback(savetex,ws))  # テクスチャフォルダの指定（画像を格納しているフォルダ）
                ws['button1'] = pm.button(c=pm.Callback(texPath,ws))
                
            with pm.horizontalLayout():
                ws['button2'] = pm.button(c=pm.Callback(namereplace, ws),en=False)  # 本体の実行
                ws['button3'] =pm.button(c=pm.Callback(pm.deleteUI,winname))  # クローズボタンで閉じたときの処理
            pm.optionMenu(ws['lang'],e=True,sl=load[2])
            winlanguage(ws)
            changeswitch(ws)  # 実行可能かの確認
