import pymel.core as pm
import re
import subprocess
import pathlib
import itertools

# 接続
def baseColor(f,files,input,imgPath):  # ベースカラー
    files.outColor>>input
    pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定

def normal(f,files,input,imgPath,rs,p2t):
    if rs==1:
        normal = pm.shadingNode('aiNormalMap', asUtility=True)  # aiノーマルマップ作成
        normal.outValue>>input
    else:
        pm.delete(files)
        pm.delete(p2t)
        normal = pm.shadingNode('RedshiftNormalMap', asUtility=True)  # rsノーマルマップ作成
        normal.outDisplacementVector>>input
        normal.tex0.set(imgPath)
        return()
    pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
    pm.setAttr(files.cs,"Raw")
    pm.setAttr(files.alphaIsLuminance,1)  # アルファ値に輝度を使用
    files.outColor>>normal.input
    pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定

def height(f,files,input,inputSG,imgPath,rs,hScale):
    pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
    pm.setAttr(files.cs,"Raw")
    pm.setAttr(files.alphaIsLuminance,1)  # アルファ値に輝度を使用
    if rs==1:
        disp = pm.shadingNode('displacementShader', asUtility=True)  # Heightマップ用のディスプレイスメントを作成
        files.outAlpha>>disp.displacement
        for i in range(len(inputSG)):
        	disp.displacement>>inputSG[i].displacementShader
    else:
        disp = pm.shadingNode('RedshiftDisplacement', asUtility=True)
        files.outColor>>disp.texMap
    	for i in range(len(inputSG)):
    		disp.out>>inputSG[i].displacementShader
    disp.scale.set(hScale)
    pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定

def othertex(f,files,input,imgPath):
    pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
    pm.setAttr(files.cs,"Raw")
    pm.setAttr(files.alphaIsLuminance,1)  # アルファ値に輝度を使用
    files.outAlpha>>input
    pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定

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
    files = pm.shadingNode('file', asTexture=True,isColorManaged=True)  # Fileノード作成
    p2t = pm.shadingNode('place2dTexture', asUtility=True)  # P2Tノード作成
    pm.defaultNavigation(connectToExisting=True, source=p2t, destination=files, f=True)  # 上記のノード接続
    input = s[0]+'.'+nodeName[i]  # マテリアルのアトリビュートノード名
    inputSG = pm.listConnections(s[0],s=False,t='shadingEngine')  # シェーディングエンジンのアトリビュートノード名（Height用）
    return(files,input,inputSG,p2t)

# パスの確認
def checkPath(nodeName,fullPath,lan,s):
    path = pathlib.Path(fullPath)
    t = path.stem
    t = t.split('_')
    for i in range(len(t)):  # 画像名とがあるかチェック
        l=list(itertools.combinations(t, i))
        for j in l:
            if s[0] == str('_'.join(j)):
                return(True)
    return(False)

# テクスチャフォルダパスの調整
def projpath(nodeName,fileName,texPath,s,f,lan):
    project = pm.workspace(q=True,fn=True)  # パスの調整
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
        missfile = pm.confirmDialog(t='Error',m=errorlanguage(nodeName,lan,n)[1],b=[(errorlanguage(nodeName,lan,'')[3]),(errorlanguage(nodeName,lan,'')[4])])
        if missfile == (errorlanguage(nodeName,lan,'')[2]):
            subprocess.run("clip", input=fullPath, text=True)  # WindowsのClipを使用してクリップボードにコピー
        return (False)
    for i in fullPath:
        ch = checkPath(nodeName,i,lan,s)
        if ch==True:
            fullPath=i
            break
    else:
        pm.confirmDialog(t='Error',m=errorlanguage(nodeName,lan,'')[2],b=errorlanguage(nodeName,lan,'')[4])
        return(False)
    imgPath = str(re.sub('.*sourceimages','sourceimages',fullPath))
    return(fullPath,imgPath)

# 本体
def texplace(nodeName,fileName,texPath,lan,rs,hScale):
    s = pm.ls(sl=True)
    for i,f in enumerate(fileName):
        if s == []:
            pm.confirmDialog(t='Error',m=(errorlanguage(nodeName[i],lan,'')[0]),b=(errorlanguage(nodeName[i],lan,'')[4]))
            break
        path = projpath(nodeName[i],fileName[i],texPath,s,f,lan)
        if path==False:
            break
        nodes = nodecrate(s,i,nodeName)
        Sorttex(f,nodes[0],nodes[1],nodes[2],path[1],rs,nodes[3],hScale)

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
    lan = ws['lang'].getSelect()  # 画像形式の保存
    pm.optionVar['texlanguage'] = lan  # データをuserPrefs.melに保存

def savemat(ws):
    lan = ws['mat'].getSelect()  # 画像形式の保存
    pm.optionVar['texmaterials'] = lan  # データをuserPrefs.melに保存
    
def savescl(ws):
    scl = ws['hScale'].getValue()  # 画像形式の保存
    pm.optionVar['texhScale'] = scl  # データをuserPrefs.melに保存

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
    if (pm.optionVar(ex='texmaterials')==True):
        mat = pm.optionVar['texmaterials']
    else:
        mat = 1
    if (pm.optionVar(ex='texhScale')==True):
        hScale = pm.optionVar['texhScale']
    else:
        hScale = 0.5
    return [chlist,texpath,lan,mat,hScale]

# 入力リセット
def resetvariable(ws):
    pm.optionVar['checklist'] = [0,0,0,0,0,0,0]
    pm.optionVar['texPath'] = 'sourceimages\\texture\\'
    pm.optionVar['texlanguage'] = 1
    pm.optionVar['texmaterials'] = 1
    pm.optionVar['texhScale'] = 0.5
    for i in range(7):
        chs = 'check'+str(i+1)
        ws[chs].setValue(0)
    ws['path'].setText('sourceimages\\texture\\')
    pm.optionMenu(ws['lang'],e=True,sl=1)
    pm.optionMenu(ws['mat'],e=True,sl=1)
    winlanguage(ws)
    pm.button(ws['button2'],e=True,en=False)
    ws['hScale'].setValue(0.5)
    visibleScale(ws)

#マテリアルごとのノード、ファイル名
def materialNodeNames(v):
    if v==1:
        #ss&aiss
        names1 = ['baseColor','metalness','specularRoughness','normalCamera','displacementShader','emission','opacity']
        names2 = ['Base','Metal','Roughness','Normal','Height','Emissive','Opacity']
    elif v==2:
        #rsm
        names1 = ['diffuse_color','metalness','refl_roughness','bump_input','displacementShader','emission_color','opacity_color']
        names2 = ['Color','Metal','Roughness','Normal','Displace','Emissive','Opacity']
    elif v==3:
        #rssm
        names1 = ['base_color','metalness','refl_roughness','bump_input','displacementShader','emission_color','opacity_color']
        names2 = ['Color','Metal','Roughness','Normal','Displace','Emissive','Opacity']
    return([names1,names2])

# ノード接続用の名前変更
def namereplace(ws):
    names = materialNodeNames(ws['mat'].getSelect())
    nodeName=[]
    fileName=[]
    for i in range(7):
        checks = 'check'+str(i+1)  # チェックが入っているものだけリストにする
        if(ws[checks].getValue()):
            nodeName.append(names[0][i])
            fileName.append(names[1][i])
    texPath = ws['path'].getText()
    formats = ['','png','exr','tif']
    lan = pm.optionMenu(ws['lang'],q=True,sl=True)
    rs = ws['mat'].getSelect()
    hScale = ws['hScale'].getValue()
    texplace(nodeName,fileName,texPath,lan,rs,hScale)

# テクスチャフォルダの名前抽出
def texPath(ws):
    basepath = pathlib.Path(pm.workspace(q=True,rootDirectory=True)+'\\sourceimages\\texture')
    if basepath.exists()==False:
        basepath = pathlib.Path(pm.workspace(q=True,rootDirectory=True)+'\\sourceimages')
    chpath = pm.fileDialog2(fm=3,okc='Select',dir=basepath)
    if(chpath==None):
        return
    path2= re.sub('.*sourceimages','sourceimages',chpath[0])
    ws['path'].setText(str(path2))
    savetex(ws)

# チェックボックスが押されている時のみ実行ボタンを押せる
def visibleScale(ws):
    if(ws['check5'].getValue()):
            ws['hScale'].setVisible(1)
    else:
        ws['hScale'].setVisible(0)

# チェックボックスが押されている時のみ実行ボタンを押せる
def changeswitch(ws):
    savecheck(ws)
    visibleScale(ws)
    for i in range(7):
        checks = 'check'+str(i+1)
        if(ws[checks].getValue()):
            ws['button2'].setEnable(1)
            break
    else:
        ws['button2'].setEnable(0)

# 言語設定
def languageset(ws):
    en = ['BaseColor','Metalness','Roughness','Normal','Height','Emissive','Opacity','Texture Folder','Connect','Close','Reset','Language']
    jp = ['BaseColor','Metalness','Roughness','Normal','Height','Emissive','Opacity','テクスチャフォルダ','接続','閉じる','リセット','言語']
    if (ws['lang'].getSelect())==1:
        ln = en
    else:
        ln = jp
    if ws['mat'].getSelect() == 1:
        return(ln)
    rs = ['Color','Metalness','Roughness','Normal','DisplaceHeightField','Emissive','Opacity']
    for i in range(7):
        ln[i]= rs[i]
    return(ln)

# 言語変更
def winlanguage(ws):
    ln = languageset(ws)
    for i in range(7):
        chs = 'check'+str(i+1)
        ws[chs].setLabel(ln[i])
    for i in range(4):
        btn = 'button'+str(i+1)
        ws[btn].setLabel(ln[i+7])
    ws['lang'].setLabel(ln[11])
    savelang(ws)
    savemat(ws)

# エラー時メッセージ
def errorlanguage(nodeName,lan,fullPath):
    en = ['Plese select a Material',nodeName+' file not found.\nPlease check file path.\n'+'"'+fullPath+'"','The image file and material name do not match.\nPlease make sure you have selected the correct material.','Copy to clipboard','Close']
    jp = ['マテリアルを選択してください。',nodeName+' ファイルが見つかりません。\n以下のフォルダに画像があるかを確認してください。\n'+'"'+fullPath+'"','画像ファイルとマテリアル名が一致しません。\n正しいマテリアルを選択しているか確認してください。','クリップボードにコピー','閉じる']
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
                ws['mat'] = pm.optionMenu(l='マテリアル',cc=pm.Callback(winlanguage,ws))  # 画像形式の指定
                pm.menuItem(l="StandardSurface & aiStandardSurface")
                pm.menuItem(l="RedShiftMaterial")
                pm.menuItem(l="RedShiftStandardMaterial")
                
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
                ws['hScale'] = pm.floatSliderGrp(l='Height Scale',f=True,max=1.0,min=0.0,v=0.1,s=0.001,cc=pm.Callback(savescl,ws))
            
            with pm.horizontalLayout():
                ws['path'] = pm.textField(text=texpath,cc=pm.Callback(savetex,ws))  # テクスチャフォルダの指定（画像を格納しているフォルダ）
                ws['button1'] = pm.button(c=pm.Callback(texPath,ws))
                
            with pm.horizontalLayout():
                ws['button2'] = pm.button(c=pm.Callback(namereplace, ws),en=False)  # 本体の実行
                ws['button3'] =pm.button(c=pm.Callback(pm.deleteUI,winname))  # クローズボタンで閉じたときの処理
            pm.optionMenu(ws['lang'],e=True,sl=load[2])
            pm.optionMenu(ws['mat'],e=True,sl=load[3])
            winlanguage(ws)
            ws['hScale'].setValue(load[4])
            changeswitch(ws)  # 実行可能かの確認
            
if __name__ == '__main__':
    openWindow()
