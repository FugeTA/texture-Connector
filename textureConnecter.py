import pymel.core as pm
import os
import re
import subprocess

# 接続
def baseColor(f,files,input,imgPath):  # ベースカラー
    if(f == 'BaseColor'):
        files.outColor>>input
        pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定
def normal(f,files,input,imgPath):
    if(f == 'Normal'):  # ノーマルマップ
        normal = pm.shadingNode('aiNormalMap', asUtility=True)  # aiノーマルマップ作成
        pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
        pm.setAttr(files.cs,"Raw")
        files.outColor>>normal.input
        normal.outValue>>input
        pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定
def height(f,files,input,inputSG,imgPath):
    if(f == 'Height'):  # ハイトマップ
        pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
        pm.setAttr(files.cs,"Raw")
        disp = pm.shadingNode('displacementShader', asUtility=True)  # Heightマップ用のディスプレイスメントを作成
        files.outAlpha>>disp.displacement
        disp.displacement>>inputSG
        pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定
def othertex(f,files,input,imgPath):
    if(f in ['Emissive','Metalness','Roughness']):  # その他グレースケールテクスチャ
        pm.setAttr(files.ignoreColorSpaceFileRules,1)  # カラースペース変更、変更を固定
        pm.setAttr(files.cs,"Raw")
        files.outAlpha>>input
        pm.setAttr(files.fileTextureName,imgPath)  # Fileノードに画像を設定
        return
        
# 画像の分類
def Sorttex(f,files,input,inputSG,imgPath):
    if(f == 'BaseColor'):    
        baseColor(f,files,input,imgPath)
        return
    if(f == 'Normal'):    
        normal(f,files,input,imgPath)
        return
    if(f == 'Height'):    
        height(f,files,input,imgPath)
        return
    if(f in ['Emissive','Metalness','Roughness']):  
        othertex(f,files,input,imgPath)
    
# ノード作成
def nodecrate(s,i,nodeName):
    files = pm.shadingNode('file', asTexture=True,isColorManaged=True)  # Fileノード作成
    p2t = pm.shadingNode('place2dTexture', asUtility=True)  # P2Tノード作成
    pm.defaultNavigation(connectToExisting=True, source=p2t, destination=files, f=True)  # 上記のノード接続
    input = s[0]+'.'+nodeName[i]  # マテリアルのアトリビュートノード名
    inputSG = s[0]+'SG.'+nodeName[i]  # シェーディングエンジンのアトリビュートノード名（Height用）
    return(files,input,inputSG)
    
    
    
# パスの確認
def checkPath(fullPath):
    if os.path.isfile(fullPath)==False:  # 設定されたパスに画像があるかチェック
        missfile = pm.confirmDialog(t='Error',m=('Image file not found.\nPlease select material and check file path.\n'+'"'+fullPath+'"'),b=['Copy to clipboard','Close'])
        if missfile == 'Copy to clipboard':
            subprocess.run("clip", input=fullPath, text=True)
    return (os.path.isfile(fullPath))
            
# テクスチャフォルダパスの調整
def projpath(texPath,name,s,f,imgformat):
    project = pm.workspace(q=True,fn=True)  # パスの調整
    project = str(project.replace('/','\\')+'\\')
    imgPath = str(texPath+'/'+name+'_'+s[0]+'_'+f+'.'+imgformat)
    imgPath = imgPath.replace('/','\\')
    fullPath = str(project+imgPath)
    return(fullPath,imgPath)

# 本体
def texplace(nodeName,fileName,texPath,name,imgformat):
    s = pm.ls(sl=True)
    
    if s == []:
        pm.confirmDialog(t='Error',m=('Plese select a Material'),b='Close')
        return
    
    for i,f in enumerate(fileName):
        path = projpath(texPath,name,s,f,imgformat)
        if checkPath(path[0])==False:
            break
        nodes = nodecrate(s,i,nodeName)
        Sorttex(f,nodes[0],nodes[1],nodes[2],path[1])

# 変数の記憶
def savecheck(ws):
    chlist = [0,0,0,0,0,0]
    for i,c in enumerate(chlist):  # チェックリストの保存
        chs = 'check'+str(i+1)
        chlist[i] = ws[chs].getValue()
    pm.optionVar['checklist'] = chlist  # データをuserPrefs.melに保存
def savetex(ws):
    if ws['path'].getText() != 'sourceimages/texture/':  # テクスチャフォルダパスの保存
        path = ws['path'].getText()  # データをuserPrefs.melに保存
    else:
        path = 'sourceimages\\texture\\'
    pm.optionVar['texPath'] = path  # データをuserPrefs.melに保存
def savefbx(ws):
    if ws['fbx'].getText() != '':  # FBXファイルパスの保存
        fbx = ws['fbx'].getText()
    else:
        fbx= ''
    pm.optionVar['fbxPath'] = fbx  # データをuserPrefs.melに保存
def saveformat(ws):
    imgformat = pm.optionMenu(ws['format'],q=True,sl=True)  # 画像形式の保存
    pm.optionVar['imgformat'] = imgformat  # データをuserPrefs.melに保存

# 変数の呼び出し
def loadvar():
    if (pm.optionVar(ex='checklist')==True):  # 前回の設定読み込みまたは新規で作成
        chlist = pm.optionVar['checklist']
    else:
        chlist = [0,0,0,0,0,0]
    if (pm.optionVar(ex='texPath')==True):
        texpath = pm.optionVar['texPath']
    else:
        texpath = 'sourceimages\\texture\\'
    if (pm.optionVar(ex='fbxPath')==True):
        fbxpath = pm.optionVar['fbxPath']
    else:
        fbxpath = ''
    if (pm.optionVar(ex='imgformat')==True):
        imgformat = pm.optionVar['imgformat']
    else:
        imgformat = 1
    return [chlist,texpath,fbxpath,imgformat]

# 入力リセット
def resetvariable(ws):
    pm.optionVar['checklist'] = [0,0,0,0,0,0]
    pm.optionVar['texPath'] = 'sourceimages\\texture\\'
    pm.optionVar['fbxPath'] = ''
    pm.optionVar['imgformat'] = 1
    for i in range(6):
        chs = 'check'+str(i+1)
        ws[chs].setValue(0)
    ws['path'].setText('sourceimages\\texture\\')
    ws['fbx'].setText('')
    pm.optionMenu(ws['format'],e=True,sl=1)
    pm.button(ws['button1'],e=True,en=False)

# ノード接続用の名前変更
def namereplace(ws):
    names1 = ['baseColor','emission','specular','specularRoughness','normalCamera','displacementShader']
    names2 = ['BaseColor','Emissive','Metalness','Roughness','Normal','Height']
    nodeName=[]
    fileName=[]
    for i in range(6):
        checks = 'check'+str(i+1)  # チェックが入っているものだけリストにする
        if(ws[checks].getValue()):
            nodeName.append(names1[i])
            fileName.append(names2[i])
    texPath = ws['path'].getText()
    name = ws['fbx'].getText()
    formats = ['','png','exr','tif']
    imgformat = formats[(pm.optionMenu(ws['format'],q=True,sl=True))]
    texplace(nodeName,fileName,texPath,name,imgformat)

# テクスチャフォルダの名前抽出
def texPath(ws):
    path = pm.fileDialog2(fm=3,okc='Select',dir=(pm.workspace(q=True,rootDirectory=True)+'\\sourceimages\\texture'))
    path2= re.sub('.*sourceimages','sourceimages',path[0])
    ws['path'].setText(str(path2))
    savetex(ws)

# FBXファイルの名前抽出
def fbxPath(ws):
    path = pm.fileDialog2(fm=1,okc='Select',dir=(pm.workspace(q=True,rootDirectory=True)))
    path2= os.path.splitext(os.path.basename(path[0]))[0]
    ws['fbx'].setText(str(path2))
    savefbx(ws)

# チェックボックスが押されている時のみ実行ボタンを押せる
def changeswich(ws):
    savecheck(ws)
    for i in range(6):
        checks = 'check'+str(i+1)
        if(ws[checks].getValue()):
            pm.button(ws['button1'],e=True,en=True)
            break
    else:
        pm.button(ws['button1'],e=True,en=False)

# ウィンドウ作成
def openWindow():
    load = loadvar()  # 前回の変数呼び出し
    ch1,ch2,ch3,ch4,ch5,ch6 = load[0]
    texpath = load[1]
    fbxpath = load[2]
    imgformat = load[3]
    
    winname = 'Texture_Connect'  # ウィンドウの名前
    if pm.window(winname,ex=True)==True:  # すでにウィンドウがあれば閉じてから開く
        pm.deleteUI(winname)
    with pm.window(winname):  # ウィンドウの作成
        with pm.autoLayout():
            ws = {}
            pm.button(l='Reset', c=pm.Callback(resetvariable,ws))  # リセット
            with pm.horizontalLayout():
                ws['check1'] = pm.checkBox(l='BaseColor',v=ch1,cc=pm.Callback(changeswich,ws))  # 接続したい画像の指定
                ws['check2'] = pm.checkBox(l='Emissive',v=ch2,cc=pm.Callback(changeswich,ws))
                ws['check3'] = pm.checkBox(l='Metalness',v=ch3,cc=pm.Callback(changeswich,ws))
            with pm.horizontalLayout():
                ws['check4'] = pm.checkBox(l='Roughness',v=ch4,cc=pm.Callback(changeswich,ws))
                ws['check5'] = pm.checkBox(l='Normal',v=ch5,cc=pm.Callback(changeswich,ws))
                ws['check6'] = pm.checkBox(l='Height',v=ch6,cc=pm.Callback(changeswich,ws))
                
            with pm.horizontalLayout():
                ws['path'] = pm.textField(ann='TextureFolder',text=texpath,cc=pm.Callback(savetex,ws))  # テクスチャフォルダの指定（画像を格納しているフォルダ）
                pm.button(l='Texture Folder',c=pm.Callback(texPath,ws))
            with pm.horizontalLayout():
                ws['fbx'] = pm.textField(ann='FBXFile',text=fbxpath,cc=pm.Callback(savefbx,ws))  # FBXファイルの指定
                pm.button(l='FBX file', c=pm.Callback(fbxPath,ws))
                
            ws['format'] = pm.optionMenu(l='ImageFormat',cc=pm.Callback(saveformat,ws))  # 画像形式の指定
            ws['menu1'] = pm.menuItem(l="PNG")
            ws['menu2'] = pm.menuItem(l="EXR")
            ws['menu3'] = pm.menuItem(l="TIFF")
            pm.optionMenu(ws['format'],e=True,sl=imgformat)  # 画像形式の呼び出し
            
            with pm.horizontalLayout():
                ws['button1'] = pm.button(l='Connect', c=pm.Callback(namereplace, ws),en=False)  # 本体の実行
                pm.button(l='Close', c=pm.Callback(pm.deleteUI,winname))  # クローズボタンで閉じたときの処理
            changeswich(ws)  # 実行可能かの確認
openWindow()
