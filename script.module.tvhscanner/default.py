import xbmc, xbmcgui, urllib, urllib2, json, sqlite3, os, xbmcaddon

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

class GUI(xbmcgui.WindowXML):



    satliste=list()
    tntliste=list()
    etapeParamTV=None
    has_recherche=0
    has_channelmap=0
    paramTVDiseqc=""
    paramTVTete=""
    paramTVSatellite=""
    initialMuxes=0
    totalMuxes=0
    totalServices=0
    adapters=list()
    selected_adapter=""
    selected_adaptername=""
    selected_type=""
    hts_host=""
    hts_port=""
    hts_user=""
    hts_pass=""
    addset=None
    top_level_url=""

    def __init__(self,strXMLname, strFallbackPath, strDefaultName="Default", forceFallback="False"):
        # Changing the three varibles passed won't change, anything
        # Doing strXMLname = "bah.xml" will not change anything.
        # don't put GUI sensitive stuff here (as the xml hasn't been read yet
        # Idea to initialize your variables here
        self.adset = xbmcaddon.Addon(id='script.module.tvhscanner')        

        settings = xbmcaddon.Addon(id='pvr.hts')


        if settings:
            self.hts_host = settings.getSetting("host")
            self.hts_port = settings.getSetting("http_port")
            self.hts_user = settings.getSetting("user")  
            self.hts_pass = settings.getSetting("pass")

            self.top_level_url = "http://"+self.hts_host+":"+self.hts_port+"/"
            if self.hts_user!="":
                # create a password manager
                password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

                # Add the username and password.    
                password_mgr.add_password(None, top_level_url, self.hts_user, self.hts_pass)

                handler = urllib2.HTTPBasicAuthHandler(password_mgr)

                # create "opener" (OpenerDirector instance)
                opener = urllib2.build_opener(handler)

                # Install the opener.
                # Now all calls to urllib2.urlopen use our opener.
                urllib2.install_opener(opener)
 
            # get adapters identifiers list

            self.adapters=self.getAdaptersInfo()
        else:
            self.message(self.adset.getLocalizedString(666001))
            self.close()
        pass

 
    def onInit(self):
        self.etapeParamTV="1"
        xbmc.executebuiltin("Skin.SetString(EtapeParamTV,1)")
        xbmc.executebuiltin("Skin.SetString(AnimationToggle,0)")

        for adapt in self.adapters:
            if adapt['deliverySystem']=="DVB-S":
                self.selected_adapter=adapt['identifier']

        # get satellite list
        if self.selected_adapter!='':
            values = {'adapter' : self.selected_adapter,'node' : 'geo'}
            data = urllib.urlencode(values) 
            req = urllib2.Request(self.top_level_url+'dvbnetworks',data)
            response = urllib2.urlopen(req)
            resp = response.read()
            oresp=json.loads(resp,strict=0)

            for sat in oresp:
                self.satliste.append({'id': sat["id"], 'text': sat['text']}) # {id, leaf, text}

        # get terrestrial list

        for adapt in self.adapters:
            if adapt['deliverySystem']=="DVB-T":
                self.selected_adapter=adapt['identifier']

        if self.selected_adapter!='':
            values = {'adapter' : self.selected_adapter,'node' : 'root'}
            data = urllib.urlencode(values) 
            req = urllib2.Request(self.top_level_url+'dvbnetworks',data)
            response = urllib2.urlopen(req)
            resp = response.read()
            osat=json.loads(resp,strict=0)

            for sat in osat:
                values = {'adapter' : self.selected_adapter,'node' : sat["id"]}
                data = urllib.urlencode(values) 
                req = urllib2.Request(self.top_level_url+'dvbnetworks',data)
                response = urllib2.urlopen(req)
                resp = response.read()
                oleaf=json.loads(resp,strict=0)
                for ssat in oleaf:
                    self.tntliste.append({'id': ssat["id"], 'text': sat["text"]+"-"+ssat['text']})  # {id, leaf, text}
          
        self.has_recherche=self.hasRechOrMap()
        self.makelistsNoAnimate()
        pass 

    def setEtape(self,etape):
        xbmc.executebuiltin("Skin.SetString(EtapeParamTV,"+etape+")")
        self.etapeParamTV=etape
        pass

    def getEtape(self):
        return self.etapeParamTV
        pass

    def hasChannelMap(self):
            return self.has_channelmap

    def getAdaptersInfo(self):
        values = {'query' : ''}

        # test if muxes are being scanned
        data = urllib.urlencode(values) 
        req = urllib2.Request(self.top_level_url+'tv/adapter',data)
        response = urllib2.urlopen(req)
        adapter = response.read()
        oadapter=json.loads(adapter,strict=0)
        self.has_recherche=0
        entries=oadapter['entries']
        return entries

    def hasRecherche(self):
        self.initialMuxes=0
        self.totalMuxes=0
        self.totalServices=0
        self.has_recherche=0
        entries=self.getAdaptersInfo()
        for adapt in entries:
            if int(adapt["initialMuxes"])>0:
                self.initialMuxes=int(adapt["initialMuxes"])
                self.totalMuxes=int(adapt["muxes"])
                self.totalServices=int(adapt["services"])
                self.has_recherche=1        

        return self.has_recherche

    def hasRechOrMap(self):
        has_recherche=self.hasRecherche()
        if has_recherche==0:
            has_recherche=self.hasChannelMap()
        return has_recherche

    def makelistsNoAnimate(self):
        val=self.getEtape()  
        xbmc.sleep(500)
        self.getControl(90060).reset()
        self.getControl(90061).reset()
        if self.has_recherche:
            listeg=self.getControl(90060)
            listeg.addItem(self.adset.getLocalizedString(666019))
            doit=1
            while (doit):
                self.updateInfos()
                xbmc.sleep(1000)
                doit=self.hasRecherche()

            if not self.hasChannelMap():
                values = {'op' : 'serviceprobe'}

                data = urllib.urlencode(values) 
                req = urllib2.Request(self.top_level_url+'dvb/adapter/'+self.selected_adapter,data)
                response = urllib2.urlopen(req)
                resp = response.read()
            doit=self.hasChannelMap()
            while doit:
                self.updateChannelInfos()
                xbmc.sleep(1000)
                doit=self.hasChannelMap()

            self.has_recherche=0
            self.makelistsNoAnimate()
        else:
            xbmc.executebuiltin("Skin.SetString(Recherche,0)") 
             
            if val=="1":
                listeg=self.getControl(90060)
                listeg.addItem(self.adset.getLocalizedString(666003))
                listeg.addItem(self.adset.getLocalizedString(666004))
                self.getControl(90062).setLabel(self.adset.getLocalizedString(666009))
                self.setFocus(listeg)
            elif val=="2":
                listeg=self.getControl(90060)
                listeg.addItem(self.adset.getLocalizedString(666003))
                listed=self.getControl(90061)
                for adapt in self.adapters:
                    litem=xbmcgui.ListItem(label=adapt["name"], label2=adapt["identifier"])
                    litem.setProperty("type",adapt["deliverySystem"])
                    listed.addItem(litem)
                self.getControl(90062).setLabel(self.adset.getLocalizedString(666010))
                self.setFocus(listed)
            elif val=="3":
                listeg=self.getControl(90060)
                listeg.addItem(self.adset.getLocalizedString(666003))
                listeg.addItem(self.selected_adaptername)
                listeg.addItem(self.adset.getLocalizedString(666012))
                listed=self.getControl(90061)
                listed.addItem("Universal")
                listed.addItem("DBS")
                listed.addItem("Standard")
                listed.addItem("Enhanced")
                listed.addItem("C-Band")
                listed.addItem("C-Multi")
                listed.addItem("Circular 10750")
                self.getControl(90062).setLabel(self.adset.getLocalizedString(666011))
                listeg.selectItem(2)
                self.setFocus(listed)
            elif val=="4":
                listeg=self.getControl(90060)
                listeg.addItem(self.adset.getLocalizedString(666003))
                listeg.addItem(self.selected_adaptername)
                listeg.addItem(self.adset.getLocalizedString(666012))
                listeg.addItem(self.adset.getLocalizedString(666014))
                listed=self.getControl(90061)
                if self.selected_type=="DVB-S":
                    for sat in self.satliste:
                        litem=xbmcgui.ListItem(label=sat["text"], label2=sat["id"])
                        listed.addItem(litem)
                else:
                    for sat in self.tntliste:
                        litem=xbmcgui.ListItem(label=sat["text"], label2=sat["id"])
                        listed.addItem(litem)                    
                self.getControl(90062).setLabel(self.adset.getLocalizedString(666015))
                listeg.selectItem(3)
                self.setFocus(listed)
            elif val=="5":
                listeg=self.getControl(90060)
                listeg.addItem(self.adset.getLocalizedString(666003))
                listeg.addItem(self.selected_adaptername)
                listeg.addItem(self.adset.getLocalizedString(666012))
                listeg.addItem(self.adset.getLocalizedString(666014))
                listeg.addItem(self.adset.getLocalizedString(666016))
                listed=self.getControl(90061)
                listed.addItem("DiSEqC 1.1 / 2.1")
                listed.addItem("DiSEqC 1.0 / 2.0")
                self.getControl(90062).setLabel(self.adset.getLocalizedString(666017))
                listeg.selectItem(4)
                self.setFocus(listed)
            elif val=="6":
                listeg=self.getControl(90060)
                listeg.addItem(self.adset.getLocalizedString(666003))
                listeg.addItem(self.selected_adaptername)
                listeg.addItem(self.adset.getLocalizedString(666012))
                listeg.addItem(self.adset.getLocalizedString(666014))
                listeg.addItem(self.adset.getLocalizedString(666016))
                listeg.addItem(self.adset.getLocalizedString(666018))
                listed=self.getControl(90061)
                listed.addItem(self.adset.getLocalizedString(666020))
                self.getControl(90062).setLabel(self.adset.getLocalizedString(666021))
                listeg.selectItem(5)
                self.setFocus(listed)
        pass

    def makelists(self):     
        xbmc.executebuiltin("Skin.SetString(AnimationToggle,1)") 
        self.makelistsNoAnimate()
        xbmc.executebuiltin("Skin.SetString(AnimationToggle,0)") 
        pass
 
    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or action==ACTION_NAV_BACK:
            self.close()
        pass
 
    def onClick(self, controlID):
        val=self.getEtape()

        if controlID==90060:
            ctrl=self.getControl(controlID)
            if (not self.has_recherche):                
                if val=="1":
                    position=ctrl.getSelectedPosition()
                    if position==0:
                        self.setEtape("2")
                        self.makelists()
                    else:
                        self.message(self.adset.getLocalizedString(666000))
                else:
                    self.setEtape(str(ctrl.getSelectedPosition()+1))
                    self.makelists()
        elif controlID==90061:
            if val=="2":
                ctrl=self.getControl(controlID)
                self.selected_adaptername=ctrl.getSelectedItem().getLabel()
                self.selected_adapter=ctrl.getSelectedItem().getLabel2()
                self.selected_type=ctrl.getSelectedItem().getProperty("type")
                self.setEtape("3")
                self.makelists()
            elif val=="3":
                ctrl=self.getControl(controlID)
                self.paramTVTete=ctrl.getSelectedItem().getLabel()
                self.setEtape("4")
                self.makelists()
            elif val=="4":
                ctrl=self.getControl(controlID)
                self.paramTVSatellite=ctrl.getSelectedItem().getLabel2()
                self.setEtape("5")
                self.makelists()
            elif val=="5":
                ctrl=self.getControl(controlID)
                self.paramTVDiseqc=ctrl.getSelectedItem().getLabel()
                self.setEtape("6")
                self.makelists()
            elif val=="6":
                self.startRecherche()
                self.has_recherche=self.hasRecherche()
                self.makelists()
        pass


    def saveDiseqc(self):
        values = {'op' : 'save', 'name' : self.selected_adaptername, 'automux' : 'on', 'idlescan' : 'on', 'qmon' : 'off', 'nitoid' : '0', 'diseqcversion' : self.paramTVDiseqc}

        # test if muxes are being scanned
        data = urllib.urlencode(values) 
        req = urllib2.Request(self.top_level_url+'dvb/adapter/'+self.selected_adapter,data)
        response = urllib2.urlopen(req)
        adapter = response.read()
        oadapter=json.loads(adapter,strict=0)
        pass

    def saveLNB(self):
        values = {'op' : 'update', 'table' : 'dvbsatconf/'+self.selected_adapter, 'entries' : '[{"lnb":"'+self.paramTVTete+'","id":"0"}]'}

        # test if muxes are being scanned
        data = urllib.urlencode(values) 
        req = urllib2.Request(self.top_level_url+'tablemgr',data)
        response = urllib2.urlopen(req)
        adapter = response.read()

        pass

    def updateInfos(self):
            xbmc.executebuiltin("Skin.SetString(Recherche,1)") 
            self.getControl(90062).setLabel("")
            values = {'op' : 'get'}

            self.getControl(90064).setLabel(str(self.totalServices))
            self.getControl(90066).setPercent(((self.totalMuxes-self.initialMuxes)*100)/(self.totalMuxes+1))
            # test if muxes are being scanned
            data = urllib.urlencode(values) 
            req = urllib2.Request(self.top_level_url+'dvb/services/'+self.selected_adapter,data)
            response = urllib2.urlopen(req)
            adapter = response.read()
            oadapter=json.loads(adapter,strict=0)
            entries=oadapter['entries']
            nb=len(entries)
            nbfound=0
            chaine=""
            while nb>0 and nbfound<5:
                try:
                    if entries[nb-1]["svcname"]!="":                        
                        chaine=chaine+entries[nb-1]["svcname"]+"\n"
                        nbfound=nbfound+1
                except Exception:
                    pass
                nb=nb-1
            self.getControl(90065).setLabel(chaine)
            pass

    def updateChannelInfos(self):
            xbmc.executebuiltin("Skin.SetString(Recherche,1)") 
            self.getControl(90062).setLabel("")
            values = {'op' : 'list'}

            data = urllib.urlencode(values) 
            req = urllib2.Request(self.top_level_url+'channels',data)
            response = urllib2.urlopen(req)
            adapter = response.read()
            oadapter=json.loads(adapter,strict=0)
            entries=oadapter['entries']
            nb=len(entries)
            totalNb=nb
            nbfound=0
            chaine=""
            while nb>0 and nbfound<5:
                try:
                    if entries[nb-1]["name"]!="":                        
                        chaine=chaine+entries[nb-1]["name"]+"\n"
                        nbfound=nbfound+1
                except Exception:
                    pass
                nb=nb-1
            self.getControl(90065).setLabel(self.adset.getLocalizedString(666023)+"\n\n"+chaine)
            self.getControl(90064).setLabel(str(totalNb))
            self.getControl(90066).setPercent(((self.totalServices-totalNb)*100)/self.totalServices)
            pass

    def startRecherche(self):
        
        if self.selected_type=="DVB-S":
            self.saveDiseqc()
            self.saveLNB()
            values = {'network' : self.paramTVSatellite, 'satconf' : '0', 'op' : 'addnetwork'}
        else:
            values = {'network' : self.paramTVSatellite, 'satconf' : '', 'op' : 'addnetwork'}

        self.has_recherche=1

        # test if muxes are being scanned
        data = urllib.urlencode(values) 
        req = urllib2.Request(self.top_level_url+'dvb/adapter/'+self.selected_adapter,data)
        response = urllib2.urlopen(req)
        adapter = response.read()
        oadapter=json.loads(adapter,strict=0)

        self.makelistsNoAnimate()
        pass


    def onFocus(self, controlID):
        pass

    def message(self, mess):
        dialog = xbmcgui.Dialog()
        dialog.ok("Information", mess)
        pass

scriptDir = xbmcaddon.Addon('script.module.tvhscanner').getAddonInfo('path')
ui = GUI('tvsetup.xml', scriptDir)
ui.doModal()
del ui


