import maya.cmds as cmds
from functools import partial
import re
import subprocess
import pathlib
import itertools

# 接続
def baseColor(f,files,input,imgPath):  # ベースカラー
    cmds.connectAttr((files+'.outColor'),input,f=True)
    cmds.setAttr((files+'.fileTextureName'),imgPath,type='string')  # Fileノードに画像を設定

def normal(f,files,input,imgPath,rs,p2t):
    if rs==1:
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
    if rs==1:
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
        missfile = cmds.confirmDialog(t='Error',m=errorlanguage(nodeName,lan,n)[1],b=[(errorlanguage(nodeName,lan,'')[3]),(errorlanguage(nodeName,lan,'')[4])])
        if missfile == (errorlanguage(nodeName,lan,'')[2]):
            subprocess.run("clip", input=fullPath, text=True)  # WindowsのClipを使用してクリップボードにコピー
        return (False)
    for i in fullPath:
        ch = checkPath(nodeName,i,lan,s)
        if ch==True:
            fullPath=i
            break
    else:
        cmds.confirmDialog(t='Error',m=errorlanguage(nodeName,lan,'')[2],b=errorlanguage(nodeName,lan,'')[4])
        return(False)
    imgPath = str(re.sub('.*sourceimages','sourceimages',fullPath))
    return(fullPath,imgPath)

# 本体
def texplace(nodeName,fileName,texPath,lan,rs,hScale):
    s = cmds.ls(sl=True)
    for i,f in enumerate(fileName):
        if s == []:
            cmds.confirmDialog(t='Error',m=(errorlanguage(nodeName[i],lan,'')[0]),b=(errorlanguage(nodeName[i],lan,'')[4]))
            break
        path = projpath(nodeName[i],fileName[i],texPath,s,f,lan)
        if path==False:
            break
        nodes = nodecrate(s,i,nodeName)
        Sorttex(f,nodes[0],nodes[1],nodes[2],path[1],rs,nodes[3],hScale)

# 変数の記憶
def savecheck(ws):
    chlist = [0,0,0,0,0,0,0]
    cmds.optionVar(ia='checklist')
    for i in range(len(chlist)):  # チェックリストの保存
        chs = 'check'+str(i+1)
        bool = cmds.checkBox(ws[chs],q=True,v=True)
        cmds.optionVar(iva=['checklist',bool])  # データをuserPrefs.melに保存

def savetex(ws):
    if cmds.textField(ws['path'],q=True,text=True) != 'sourceimages/texture/':  # テクスチャフォルダパスの保存
        path = cmds.textField(ws['path'],q=True,text=True)  # データをuserPrefs.melに保存
    else:
        return()
    cmds.optionVar(sv=['texPath',path])  # データをuserPrefs.melに保存

def savelang(ws):
    lan = cmds.optionMenu(ws['lang'],q=True,sl=True)  # 画像形式の保存
    cmds.optionVar(iv=['texlanguage',lan])  # データをuserPrefs.melに保存

def savemat(ws):
    lan = cmds.optionMenu(ws['mat'],q=True,sl=True)  # 画像形式の保存
    cmds.optionVar(iv=['texmaterials',lan])  # データをuserPrefs.melに保存
    
def savescl(ws,*args):
    scl = cmds.floatSliderGrp(ws['hScale'],q=True,v=True)  # 画像形式の保存
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
def resetvariable(ws,*args):
    cmds.optionVar(ia=['checklist'])
    cmds.optionVar(sv=['texPath','sourceimages\\texture\\'])
    cmds.optionVar(iv=['texlanguage',1])
    cmds.optionVar(iv=['texmaterials',1])
    cmds.optionVar(fv=['texhScale',0.5])
    for i in range(7):
        chs = 'check'+str(i+1)
        cmds.checkBox(ws[chs],e=True,v=0)
    cmds.textField(ws['path'],e=True,text='sourceimages\\texture\\')
    cmds.optionMenu(ws['lang'],e=True,sl=1)
    cmds.optionMenu(ws['mat'],e=True,sl=1)
    winlanguage(ws)
    cmds.button(ws['button2'],e=True,en=False)
    cmds.floatSliderGrp(ws['hScale'],e=True,v=0.5)
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
def namereplace(ws,*args):
    names = materialNodeNames(cmds.optionMenu(ws['mat'],q=True,sl=True))
    nodeName=[]
    fileName=[]
    for i in range(7):
        checks = 'check'+str(i+1)  # チェックが入っているものだけリストにする
        if(cmds.checkBox(ws[checks],q=True,v=True)):
            nodeName.append(names[0][i])
            fileName.append(names[1][i])
    texPath = cmds.textField(ws['path'],q=True,tx=True)
    formats = ['','png','exr','tif']
    lan = cmds.optionMenu(ws['lang'],q=True,sl=True)
    rs = cmds.optionMenu(ws['mat'],q=True,sl=True)
    hScale = cmds.floatSliderGrp(ws['hScale'],q=True,v=True)
    texplace(nodeName,fileName,texPath,lan,rs,hScale)

# テクスチャフォルダの名前抽出
def texPath(ws,*args):
    basepath = pathlib.Path(cmds.workspace(q=True,rootDirectory=True)+'\\sourceimages\\texture')
    if basepath.exists()==False:
        basepath = pathlib.Path(cmds.workspace(q=True,rootDirectory=True)+'\\sourceimages')
    chpath = cmds.fileDialog2(fm=3,okc='Select',dir=basepath)
    if(chpath==None):
        return
    path2= re.sub('.*sourceimages','sourceimages',chpath[0])
    cmds.textField(ws['path'],e=True,text=str(path2))
    savetex(ws)

# チェックボックスが押されている時のみ実行ボタンを押せる
def visibleScale(ws):
    if(cmds.checkBox(ws['check5'],q=True,v=True)):
        cmds.floatSliderGrp(ws['hScale'],e=True,vis=1)
    else:
        cmds.floatSliderGrp(ws['hScale'],e=True,vis=0)

# チェックボックスが押されている時のみ実行ボタンを押せる
def changeswitch(ws,*args):
    savecheck(ws)
    visibleScale(ws)
    for i in range(7):
        checks = 'check'+str(i+1)
        if(cmds.checkBox(ws[checks],q=True,v=True)):
            cmds.button(ws['button2'],e=True,en=1)
            break
    else:
        cmds.button(ws['button2'],e=True,en=0)

# 言語設定
def languageset(ws,*args):
    en = ['BaseColor','Metalness','Roughness','Normal','Height','Emissive','Opacity','Texture Folder','Connect','Close','Reset','Language']
    jp = ['BaseColor','Metalness','Roughness','Normal','Height','Emissive','Opacity','テクスチャフォルダ','接続','閉じる','リセット','言語']
    if cmds.optionMenu(ws['lang'],q=True,sl=True)==1:
        ln = en
    else:
        ln = jp
    if cmds.optionMenu(ws['mat'],q=True,sl=True) == 1:
        return(ln)
    rs = ['Color','Metalness','Roughness','Normal','DisplaceHeightField','Emissive','Opacity']
    for i in range(7):
        ln[i]= rs[i]
    return(ln)

# 言語変更
def winlanguage(ws,*args):
    ln = languageset(ws)
    for i in range(7):
        chs = 'check'+str(i+1)
        cmds.checkBox(ws[chs],e=True,l=(ln[i]))
    for i in range(4):
        btn = 'button'+str(i+1)
        cmds.button(ws[btn],e=True,l=(ln[i+7]))
    cmds.optionMenu(ws['lang'],e=True,l=(ln[11]))
    savelang(ws)
    savemat(ws)

# エラー時メッセージ
def errorlanguage(nodeName,lan,fullPath):
    en = ['Plese select a Material',nodeName+' file not found.\nPlease check file path.\n'+'"'+fullPath+'"','The image file and material name do not match.\nPlease make sure you have selected the correct material.','Copy to clipboard','Close']
    jp = ['マテリアルを選択してください。',nodeName+' ファイルが見つかりません。\n以下のフォルダに画像があるかを確認してください。\n'+'"'+fullPath+'"','画像ファイルとマテリアル名が一致しません。\n正しいマテリアルを選択しているか確認してください。','クリップボードにコピー','閉じる']
    if lan==1:
        return en
    return jp

def closewindow(name,*args):
    cmds.deleteUI(name,window=True)

# ウィンドウ作成
def openWindow():
    load = loadvar()  # 前回の変数呼び出し
    try:
        ch1,ch2,ch3,ch4,ch5,ch6,ch7 = load[0]
    except TypeError:
        ch1,ch2,ch3,ch4,ch5,ch6,ch7 = [0,0,0,0,0,0,0]
    texpath = load[1]
    
    ws = {}
    winname = 'Texture_Connect'  # ウィンドウの名前
    if cmds.window(winname,q=True,ex=True)==True:  # すでにウィンドウがあれば閉じてから開く
        cmds.deleteUI(winname,window=True)
    cmds.window(winname,s=True,rtf=True)  # ウィンドウの作成
    form = cmds.formLayout()
    column = cmds.columnLayout()
    
    r1 = cmds.rowLayout(nc=2)
    ws['lang'] = cmds.optionMenu(l='言語',cc=partial(winlanguage,ws))  # 画像形式の指定
    cmds.menuItem(l="English")
    cmds.menuItem(l="日本語")
    ws['button4'] = cmds.button(c=partial(resetvariable,ws))  # リセット
    cmds.setParent('..')
    
    r2 = cmds.rowLayout(nc=1)
    ws['mat'] = cmds.optionMenu(l='マテリアル',cc=partial(winlanguage,ws))  # 画像形式の指定
    cmds.menuItem(l="StandardSurface & aiStandardSurface")
    cmds.menuItem(l="RedShiftMaterial")
    cmds.menuItem(l="RedShiftStandardMaterial")
    cmds.setParent('..')
                
    r3 = cmds.rowLayout(nc=3)
    ws['check1'] = cmds.checkBox(v=ch1,cc=partial(changeswitch,ws))  # 接続したい画像の指定
    ws['check2'] = cmds.checkBox(v=ch2,cc=partial(changeswitch,ws))
    ws['check3'] = cmds.checkBox(v=ch3,cc=partial(changeswitch,ws))
    cmds.setParent('..')
    
    r4 = cmds.rowLayout(nc=4)
    ws['check4'] = cmds.checkBox(v=ch4,cc=partial(changeswitch,ws))
    ws['check5'] = cmds.checkBox(v=ch5,cc=partial(changeswitch,ws))
    ws['check6'] = cmds.checkBox(v=ch6,cc=partial(changeswitch,ws))
    ws['check7'] = cmds.checkBox(v=ch7,cc=partial(changeswitch,ws))
    cmds.setParent('..')
    
    r5 = cmds.rowLayout(nc=1)
    ws['hScale'] = cmds.floatSliderGrp(l='Height Scale',f=True,max=1.0,min=0.0,v=0.5,s=0.001,cc=partial(savescl,ws))
    cmds.setParent('..')
            
    r6 = cmds.rowLayout(nc=2)
    ws['path'] = cmds.textField(text=texpath,cc=partial(savetex,ws))  # テクスチャフォルダの指定（画像を格納しているフォルダ）
    ws['button1'] = cmds.button(c=partial(texPath,ws))
    cmds.setParent('..')
    
    r7 = cmds.rowLayout(nc=2)
    ws['button2'] = cmds.button(c=partial(namereplace, ws),en=False)  # 本体の実行
    ws['button3'] =cmds.button(c=partial(closewindow,winname))  # クローズボタンで閉じたときの処理
    cmds.setParent('..')
    
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.formLayout(form,e=True,attachForm=[(column,'top',5),(column,'left',5),(column,'right',5),(column,'bottom',5)])

    cmds.optionMenu(ws['lang'],e=True,sl=load[2])
    cmds.optionMenu(ws['mat'],e=True,sl=load[3])
    winlanguage(ws)
    cmds.floatSliderGrp(ws['hScale'],e=True,v=load[4])
    changeswitch(ws)  # 実行可能かの確認
    cmds.showWindow()
    
if __name__ == '__main__':
    openWindow()

