from Tkinter import *
from common import *
import game
import dialog
import ai
import string

RELIEF_STYLE=RIDGE
BORDERWIDTH=1

def log(msg):
    print "<main>",msg
    
def loadImages():
    log("loading images")
    global RED_FACTORY_IMAGE
    global BLUE_FACTORY_IMAGE
    global GREEN_FACTORY_IMAGE
    global PURPLE_FACTORY_IMAGE
    RED_FACTORY_IMAGE = PhotoImage(file="redfac.gif")
    BLUE_FACTORY_IMAGE = PhotoImage(file="bluefac.gif")
    GREEN_FACTORY_IMAGE = PhotoImage(file="greenfac.gif")
    PURPLE_FACTORY_IMAGE = PhotoImage(file="purpfac.gif")
    global FACTORY_IMAGES
    FACTORY_IMAGES = (RED_FACTORY_IMAGE, BLUE_FACTORY_IMAGE,
                      GREEN_FACTORY_IMAGE, PURPLE_FACTORY_IMAGE)

    global RED_BARREL_IMAGE
    global YELLOW_BARREL_IMAGE
    global GREEN_BARREL_IMAGE
    RED_BARREL_IMAGE = PhotoImage(file="srbarrel.gif")
    YELLOW_BARREL_IMAGE = PhotoImage(file="sybarrel.gif")
    GREEN_BARREL_IMAGE = PhotoImage(file="sgbarrel.gif")

class MainWindow:
    "the main window for the game"

    def __init__(self):
        self.app = Tk()
        loadImages()

        try:
            self.app.iconbitmap(default="barrel.ico")
        except TypeError, e:
            pass #default keyword not supported
        #self.app.option_readfile("main.config")
        self.app.title("Industrial Waste")
        self.mainloop = self.app.mainloop
        self.app.protocol("WM_DELETE_WINDOW",self.app.destroy)
        self.menu = Menu(self.app)
        self.app.config(menu=self.menu)
        self.filemenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label=string.ljust("File",MENU_LABEL_WIDTH),
                              menu=self.filemenu)
        self.filemenu.add_command(label="New Game", command=self.askNewGame)
        self.filemenu.add_command(label="Exit", command=self.app.quit)

        self.helpmenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label=string.ljust("Help",MENU_LABEL_WIDTH),
                              menu=self.helpmenu)
        self.helpmenu.add_command(label="About",command=self.showAbout)

        #create left and right panes
        self.leftPane = Frame(self.app)
        self.leftPane.grid(row=0,column=0,rowspan=8,sticky=W+N)
        self.rightPane = Frame(self.app)
        self.rightPane.grid(row=0,column=1,rowspan=8,sticky=E+N)
                            
        self.wasteTrack = WasteTrack(self.app)
        self.wasteTrack.grid(row=8,column=0,columnspan=2,sticky=W)

        self.messagePane = Frame(self.app)
        self.messagePane.grid(row=9,column=0,columnspan=2,sticky=N+S+E+W)

        self.messageScroll = Scrollbar(self.messagePane,orient=VERTICAL)
        self.messageScroll.grid(row=0,column=5,sticky=N+S)
        
        self.messageList = Listbox(self.messagePane,
                                   height=MESSAGE_LIST_HEIGHT,
                                   width=MESSAGE_LIST_WIDTH,
                                   bg=TEXT_COLOR,
                                   yscrollcommand=self.messageScroll.set)
        self.messageList.grid(row=0,column=0,columnspan=4,sticky=N+S+E+W)
        self.messageScroll["command"] = self.messageList.yview

        
        
        #fill left pane
        self.mainboard = MainBoard(self.leftPane)
        self.mainboard.grid(row=0,column=0,sticky=W,rowspan=3,ipadx=2)

        self.autoTrack = TechTrack(self.leftPane,game.AUTOMATION)
        self.autoTrack.grid(row=3,column=0,sticky=W,ipadx=2)

        self.rawUsageTrack = TechTrack(self.leftPane,
                                       game.RAW_MATERIAL_USAGE)
        self.rawUsageTrack.grid(row=4,column=0,sticky=W,ipadx=2)

        self.wasteReductionTrack = TechTrack(self.leftPane,
                                             game.WASTE_REDUCTION)
        self.wasteReductionTrack.grid(row=5,column=0,sticky=W,ipadx=2)

        self.companies = []
        self.pollID = 0
        self.winners = []

    def startPolling(self):

        if self.gameState.phase == game.PHASE_GAME_OVER:
            self.gameOver()
            return
        
        if self.gameState.phase == game.PHASE_BASIC_COSTS:
            self.basicCosts()
        
        if self.gameState.phase == game.PHASE_NEW_ROUND:
            self.gameState.nextPhase()
            self.phaseAction()
            
        if self.gameState.phase == game.PHASE_CARD_PLAY:
            current  = self.gameState.getCurrent()
            played = 0
            if len(current.cards) == 1:
                card = current.cards[0]
                if not current.canPlay(card):
                    cp = game.CardPlay(card)
                    cp.action = game.SAVE
                    self.playCard(cp)
                    played = 1
            if not played and self.controlList[current.id] == CONTROL_AI:
                cardPlay = self.ai.getCardPlay()
                self.playCard(cardPlay)

            
        self.pollID = self.app.after(500,self.startPolling)

    def cancelPolling(self):
        self.app.after_cancel(self.pollID)
        

    def postMessage(self,message):
        log(message)
        self.messageList.insert(END,message)
        size = self.messageList.size()
        if size > MESSAGE_LIST_HEIGHT:
            #self.messageList.yview_scroll(1,UNITS)
            self.messageList.yview_moveto(1.0)
            
    def askNewGame(self):
        "show the dialog for starting a new game"
        n = dialog.NewGameDialog(self.app, self.newGame)


    def newGame(self, numPlayers, nameList, colorList,controlList):
        "set up a new game; called by the new game dialog"
        self.numPlayers = numPlayers
        self.nameList = nameList
        self.colorList = colorList
        self.controlList = controlList
        log("control:" + str(controlList))
        self.gameState = game.Game(numPlayers)
        self.gameState.newGame()
        self.ai = ai.SimpleAI(self.gameState)
        
        for c in self.companies:
            c.grid_forget()
        self.companies = []
        
        for i in range(numPlayers):
            c = self.gameState.companies[i]
            
            self.companies.append(
                CompanyBoard(self.rightPane,c, nameList[i],
                             colorList[i],self.cardClick,i,
                             controlList[i]))

            self.companies[i].grid(row=i,column=1,padx=10,pady=15,sticky=N+W)

        self.gameState.newRound()
        self.update()

        #start polling
        self.cancelPolling()
        self.startPolling()

    def doAuction(self):
        log("do auction")
        while self.gameState.phase == game.PHASE_AUCTION:
            current = self.gameState.current
            auctioneer = self.gameState.auctioneer
            if self.gameState.highBidder is not None:
                highBidder = self.gameState.highBidder.id
            else:
                highBidder = 0
            if self.controlList[current] == CONTROL_AI:
                bid = self.ai.getBid()
                self.doBid(bid)
            else:
                l = dialog.BidDialog(self.app, self.gameState.auctionGoods,
                                     self.nameList[highBidder],
                                     self.colorList[highBidder],
                                     self.gameState.highBid,
                                     self.nameList[auctioneer],
                                     self.colorList[auctioneer],
                                     self.nameList[current],
                                     self.colorList[current],
                                     self.doBid)

        if self.gameState.highBid > 0:
            self.postMessage("%s wins %d goods for $%d million" %
                             ( self.nameList[self.gameState.highBidder.id],
                               self.gameState.auctionGoods,
                               self.gameState.highBid))
        self.update()

    def doBid(self,bidAmount):
        "callback for auctions"
        current = self.gameState.current
        if bidAmount > self.gameState.highBid:
            self.postMessage("%s bids $%d million" %
                             (self.nameList[current],bidAmount))
        self.gameState.bid(bidAmount)

    def phaseAction(self):
        "perform the appropriate action for the current phase"

        log("phase action")
        #accident
        if self.gameState.phase == game.PHASE_ACCIDENT:
            self.postMessage("An Accident Has Occurred!")
            if self.gameState.anyVulnerable():
                anyHumans = 0
                for i in range(self.numPlayers):
                    if self.controlList[i] == CONTROL_HUMAN:
                        anyHumans = 1
                        break
                if anyHumans:
                    l = dialog.AccidentDialog(self.app)

        #accident
        while self.gameState.phase == game.PHASE_ACCIDENT:
            currentIndex = self.gameState.current
            current = self.gameState.getCurrent()
            useBribery = [0]
            if current.hasBribery() and current.isVulnerable():
                if self.controlList[current.id] == CONTROL_AI:
                    useBribery[0] = self.ai.useBribery()
                else:
                    l = dialog.UseBriberyDialog(
                        self.app, self.nameList[currentIndex],
                        self.colorList[currentIndex],useBribery)
            fine,shrink = current.getPenalties(useBribery[0])
            if current.isVulnerable():
                self.postMessage(("%s is fined $%d million and " +
                                  "loses %d growth") %
                                 (self.nameList[current.id],fine,shrink))
            self.gameState.handleAccident(useBribery[0])
                
            self.update()


        self.update()
        #card draft
        while self.gameState.phase == game.PHASE_CARD_DRAFT:
            current = self.gameState.current
            if self.controlList[current] == CONTROL_AI:
                index = self.ai.chooseCardStack()
                self.takeCards(index)
            else:
                l = dialog.LayoutDialog(self.app, self.gameState.layout,
                                        self.nameList[current],
                                        self.colorList[current],
                                        self.takeCards)
        self.update()


    def basicCosts(self):
        "handle paying of basic costs for all companies"
        while self.gameState.phase == game.PHASE_BASIC_COSTS:
            current = self.gameState.getCurrent()
            self.postMessage("%s pays $%d million in basic costs" %
                             (self.nameList[current.id],
                              current.getBasicCosts()))
            self.gameState.payBasicCosts()
        self.update()
        


    def gameOver(self):
        "handle output of end game information"
        log("game over")
        self.update()
        maxScore = 0
        for c in self.gameState.companies:
            score = c.getScore()
            self.postMessage(
                ("%s scores %d  (growth:%d  innovation:%d  " +
                "money:%d  loans:%d)" )%
                (self.nameList[c.id],score[0],score[1],score[2],
                 score[3],score[4]))

        self.winners = self.gameState.getWinners()
        if len(self.winners) == 1:
            self.postMessage("%s Wins the Game!" %
                             self.nameList[self.winners[0].id])
        else:
            winString = ""
            punc = [""]
            punc.extend([", "] * (len(self.winners) - 2))
            punc.append(" and ")
            for i in range(len(self.winners)):
                winString = winString + punc[i] + \
                            self.nameList[self.winners[i].id]

            self.postMessage("%s Tie for the Win!" %  winString)
        self.update()
                                      

        
    def takeCards(self,stackIndex):
        "called by LayoutDialog; take cards from layout and give to company"
        current = self.gameState.current
        chosen = self.gameState.chooseLayout(stackIndex)
        msg = "%s chose %s, %s and %s" % ( self.nameList[current],
                                          chosen[0],chosen[1],chosen[2])
        self.postMessage(msg)
        self.update()


    def playCard(self,cardPlay):
        "handle play of cards"

        card = cardPlay.card
        log("play card " + card)
        current = self.gameState.current

        if cardPlay.useAdvisor:
            advisorString = "with Advisor"
        else:
            advisorString = ""
        if cardPlay.action == game.PLAY:
            self.postMessage("%s plays %s %s" %
                             (self.nameList[current],card,advisorString))
            self.gameState.playCard(cardPlay)
        elif cardPlay.action == game.DISCARD:
            self.postMessage("%s discards %s" % (self.nameList[current],card))
            self.gameState.discardCard(cardPlay.card)
        elif cardPlay.action == game.SAVE:
            self.postMessage("%s saves %s" % (self.nameList[current],card))
            self.gameState.playPass()
        self.update()
        if self.gameState.phase == game.PHASE_AUCTION:
            self.doAuction()

        
    def update(self):
        "update the main board to show company attributes"
        self.mainboard.clear()
        self.autoTrack.clear()
        self.rawUsageTrack.clear()
        self.wasteReductionTrack.clear()
        self.wasteTrack.clear()
        for i in range(self.numPlayers):
            c = self.gameState.companies[i]
            #color = self.colorList[i]
            image = FACTORY_IMAGES[i]
            self.mainboard.addMarker( c.growth,c.workers, image)

            self.autoTrack.addMarker( c.automation,image)
            self.rawUsageTrack.addMarker(c.rawMaterialUsage,image)
            self.wasteReductionTrack.addMarker(c.wasteReduction,image)
            self.wasteTrack.addMarker(c.waste,image)

            companyBoard = self.companies[i]
            companyBoard.clearHeader()
            companyBoard.update()

        if self.gameState.phase != game.PHASE_GAME_OVER:
            self.companies[ self.gameState.start ].setStartMark()
            self.companies[ self.gameState.current ].setCurrentMark()
        else:
            for w in self.winners:
                self.companies[w.id].setWinnerMark()
            for c in self.companies:
                c.showScore()

    def cardClick(self,companyIndex, card):
        if (self.gameState.phase == game.PHASE_CARD_PLAY and
            self.gameState.current == companyIndex):

            current  = self.gameState.getCurrent()
            allowPass = len(current.cards) == 1
            hasAdvisor = (game.CARD_ADVISOR in current.cards and
                          card != game.CARD_ADVISOR)
            canPlay = current.canPlay(card)

            
            l = dialog.ConfirmCardDialog(self.app,
                                         self.nameList[companyIndex],
                                         self.colorList[companyIndex],
                                         card,self.playCard,allowPass,
                                         hasAdvisor,canPlay)
    def showAbout(self):
        "display the about dialog"
        d = dialog.AboutDialog(self.app)
            

class MainBoard(Frame):    
    "a class to represent the main board, where growth and workers are tracked"

    GROWTH_COLUMNS = [14,15,16,17,18,19,20]
    COLUMNS = len(GROWTH_COLUMNS)
    WORKER_ROWS = [5,4,3,2,1]
    ROWS=len(WORKER_ROWS)
    
    def __init__(self,parent):
        Frame.__init__(self,parent, relief=RELIEF_STYLE,
                       borderwidth=BORDERWIDTH)

        Label(self,text="Company Growth",font=DEFAULT_FONT).grid(
            row=0,column=0,
            columnspan=MainBoard.COLUMNS)
        Label(self,text="Workers",font=DEFAULT_FONT).grid(row=1,column=0)

        i=1
        for gc in MainBoard.GROWTH_COLUMNS:
            Label(self,text=str(gc),font=DEFAULT_FONT).grid(row=1,column=i)
            i=i + 1

        j=2
        for wr in MainBoard.WORKER_ROWS:
            Label(self,text=str(wr),font=DEFAULT_FONT).grid(column=0,row=j)
            j = j + 1

        self.cells = []
        i=1;j=1
        for i in range(MainBoard.COLUMNS):
            self.cells.append( [])
            for j in range(MainBoard.ROWS):
                g = GridCell(self)
                g.grid(row=j+2,column=i+1)                
                self.cells[i].append(g  )

    
    def clear(self):
        for cs in self.cells:
            for c in cs:
                c.clear()

    def addMarker(self, growth, workers, image):
        i = MainBoard.GROWTH_COLUMNS.index(growth)
        j = MainBoard.WORKER_ROWS.index(workers)
        self.cells[i][j].addMarker(image)

class CompanyBoard(Frame):
    "a panel showing the info for a company"

    def __init__(self,parent,company,name,color,callback,index,control):
        Frame.__init__(self,parent,relief=RELIEF_STYLE,
                       borderwidth=BORDERWIDTH)

        self.parent = parent
        self.company = company
        self.name = name
        self.callback = callback
        self.index = index
        self.control = control
        self.title = Label(self,text=name,width=40,bg=color,fg=TEXT_COLOR,
                           font=COMPANY_NAME_FONT)
        colspan = 3
        self.title.grid(row=0,column=0,columnspan=colspan,sticky=W)
        self.title.grid_propagate(0)

        col = 0

        self.moneyLabel = Label( self,font=DEFAULT_FONT)
        self.moneyLabel.grid(row=1,column=col,sticky=W)
        col += 1

        self.rawMaterialsLabel = Label(self, font=DEFAULT_FONT)
        self.rawMaterialsLabel.grid(row=1,column=col,sticky=W)
        col += 1

        self.loansLabel = Label( self,font=DEFAULT_FONT)
        self.loansLabel.grid(row=1,column=col,sticky=W)
        col += 1

        self.updateCompany()

        self.buttonPane = Frame(self)
        self.buttonPane.grid(row=2,column=0,columnspan=4,sticky=E+W)

        self.cardButtons = []

    def update(self):
        self.updateCompany()
        self.updateCards()

    def updateCompany(self):
        "update money, loans and raw materials"
        if SHOW_ALL_MONEY or self.control == CONTROL_HUMAN:
            self.moneyLabel.config(text="$ %d million" % self.company.money)
        else:
            self.moneyLabel.config(text="$?")
        self.rawMaterialsLabel.config(
            text="%d Raw Materials" % self.company.rawMaterials)
        self.loansLabel.config(text="Loans: %d" % self.company.loans)

    def setCurrentMark(self):
        "set the widget header to indicate it is this company's turn"
        newText = "*** " + self.title.cget("text")
        self.title.config(text=newText)

    def setStartMark(self):
        "set the widget header to indicate it is the start company"
        newText = self.title.cget("text") + " (Start)"
        self.title.config(text=newText)

    def setWinnerMark(self):
        "set the widget header to indicate that this company has won"
        newText = self.title.cget("text") + " wins!"
        self.title.config(text=newText)

    def clearHeader(self):
        "set the header to be just the company name"
        self.title.config(text=self.name)

    def showScore(self):
        "display the score"
        newText = self.title.cget("text") + " " + \
                  str(self.company.getScore()[0]) + " pts."
        self.title.config(text=newText)
        
    def updateCards(self):
        "draw the current cards for this company"
        cards = self.company.cards
        for c in self.cardButtons:
            c.grid_forget()
        self.cardButtons = []
        
        for i in range(len(cards)):
            card = cards[i]
            cb = Button(self.buttonPane,text=card,
                        width=CARD_WIDTH,font=CARD_FONT,
                        relief=CARD_RELIEF,
                        bg=CARD_BACKGROUND,fg=CARD_FOREGROUND,
                        command=
                        (lambda ob=self,index=i: ob.handleClick(index)))
            self.cardButtons.append(cb)
            cb.grid(row=0,column=i,padx=2,pady=2)


    def handleClick(self,cardIndex):
        self.callback(self.index,self.company.cards[cardIndex])
        
class TechTrack(Frame):
    "a grid to show progress in one of the three innovation tracks"

    HEADERS = [ 5, 4, 3, 2, 1 ]
    def __init__(self,parent,name):
        Frame.__init__(self,parent,relief=RELIEF_STYLE,
                       borderwidth=BORDERWIDTH)

        l = Label(self,text=name,width=17,font=DEFAULT_FONT)
        l.grid(row=1,column=0)
        l.grid_propagate(0)
        self.cells = []
        for i in range(5):
            header = TechTrack.HEADERS[i]
            Label(self,text="%d/%d" % (header,
                                         game.INNOVATION_SCORING[header]),
                  font=DEFAULT_FONT).grid(row=0,column=i+1)
            g = GridCell(self)
            g.grid(row=1,column=i+1)
            self.cells.append( g)

    def clear(self):
        for c in self.cells:
            c.clear()


    def addMarker(self,level,image):
        i = TechTrack.HEADERS.index(level)
        self.cells[i].addMarker(image)

BARREL_HEIGHT=28
BARREL_WIDTH=24
class WasteTrack(Frame):
    "a grid to show how much waste each company has"
    def __init__(self,parent):
        Frame.__init__(self,parent,relief=RELIEF_STYLE,
                       borderwidth=BORDERWIDTH)

        l = Label(self,text="Waste",width=7,font=DEFAULT_FONT)
        l.grid(row=1,column=0)
        l.grid_propagate(0)
        self.cells = []

        textX = BARREL_WIDTH/2
        textY = BARREL_HEIGHT/2
        rectHeight = 13
        for i in range(17):
            if i <= 8:
                image = GREEN_BARREL_IMAGE
                rectColor = "#0f0"
                textColor = "black"
            elif i <= 12:
                image = YELLOW_BARREL_IMAGE
                rectColor = "#ff0"
                textColor = "black"
            else:
                image = RED_BARREL_IMAGE
                rectColor = "#f00"
                textColor = "white"
            if i > 9:
                rectWidth = 11
            else:
                rectWidth = 6


            canvas = Canvas(self,height=BARREL_HEIGHT,
                            width=BARREL_WIDTH)
            canvas.grid(row=0,column=i+1)
            canvas.create_image(1,1,anchor=NW,image=image)

            rectX1 = (BARREL_WIDTH - rectWidth) / 2
            rectY1 = (BARREL_HEIGHT - rectHeight) / 2
            rectX2 = rectX1 + rectWidth
            rectY2 = rectY1 + rectHeight
            canvas.create_rectangle(rectX1,rectY1,rectX2,rectY2,
                                    fill=rectColor,outline=rectColor)
            canvas.create_text(textX,textY,anchor=CENTER,text=str(i),
                               font=BARREL_FONT,fill=textColor)
            
            g = GridCell(self)
            g.grid(row=1,column=i+1)
            self.cells.append(g)
                  
    def clear(self):
        "remove all markers from track"
        for c in self.cells:
            c.clear()

    def addMarker(self,level,image):
        "add a marker at the given level"
        self.cells[ level].addMarker(image)
    
class GridCell(Canvas):
    "This is a cell designed to hold up to four company markers"
    CELL_HEIGHT=50
    CELL_WIDTH=52
    MARKER_HEIGHT=23
    MARKER_WIDTH=26
    XPAD=0
    YPAD=1
    OFFSET=4

    MARKER_POSITIONS = (   (OFFSET,OFFSET),
                           (MARKER_WIDTH + OFFSET+XPAD,OFFSET),
                           (OFFSET,MARKER_HEIGHT + OFFSET+YPAD),
                           (MARKER_WIDTH+OFFSET+XPAD,
                            MARKER_HEIGHT+OFFSET+YPAD))
    
    def __init__(self,parent):
        Canvas.__init__(self,parent,relief=GROOVE,
                        borderwidth=BORDERWIDTH,
                        height=GridCell.CELL_HEIGHT,
                        width=GridCell.CELL_WIDTH)
    

        self.markers = []
        self.images = []

    def clear(self):
        for m in self.markers:
            self.delete(m)
        self.markers = []
        del self.images
        self.images = []

    def addMarker(self,image):
        self.images.append(image)
        x1,y1 = GridCell.MARKER_POSITIONS[len(self.images) - 1]
        x2 = x1 + GridCell.MARKER_WIDTH
        y2 = y1 + GridCell.MARKER_HEIGHT
        #m = self.create_rectangle(x1,y1,x2,y2,fill=color)
        m = self.create_image(x1,y1,anchor=NW,image=image)
        self.markers.append( m)


    
        
if __name__ == "__main__":
    mw = MainWindow()
    mw.mainloop()
