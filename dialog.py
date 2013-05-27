# -*- coding:iso-8859-1 -*-
from Tkinter import *
from common import *
import game
import string

ABOUT_LINES = [
    ("Industrial Waste verson 1.0","14"),
    ("Game Design:  Jürgen Strohm","12"),
    ("Programming:  Nicholas Wieczorek","12"),
    ("Copyright 2001 Hans im Glück Verlags-GmbH","8")
    ]

class Dialog(Toplevel):
    "a class to add some dialog-type functionality to the toplevel class"

    def __init__(self,parent,title,okText="OK",cancelText="Cancel"):
        Toplevel.__init__(self,parent)
        self.transient(parent)
        self.title(title)
        self.parent = parent
        self.result = None
        self.okText = okText
        self.cancelText = cancelText

        body = Frame(self)
        self.initial_focus = self.buildBody(body)
        body.pack(padx=5,pady=5)
        
        self.buildButtonbox()
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW",self.cancel)
        self.geometry("+%d+%d" %
                      (parent.winfo_rootx()+50, parent.winfo_rooty()+50))
        self.initial_focus.focus_set()
        self.wait_window(self)



    def buildBody(self,frame):
        "override to create dialog body and return widget that should " \
                  "have initial focus"
        pass

    def buildButtonbox(self):
        "add standard ok and cancel buttons"
        box = Frame(self)
        self.addOKButton(box)
        self.addCancelButton(box)
        box.pack()

    def addOKButton(self,box):
        w = Button(box, text=self.okText,
                   width=10,command=self.ok, default=ACTIVE)
        w.pack(side=LEFT,padx=5,pady=5)
        self.bind("<Return>",self.ok)

    def addCancelButton(self,box):
        w = Button(box,text=self.cancelText,width=10,command=self.cancel)
        w.pack(side=LEFT,padx=5,pady=5)
        self.bind("<Escape>",self.cancel)
        
        

    def cancel(self,event=None):
        "event handler for cancel button"
        self.cancelTasks()
        self.close()

    def close(self):
        self.parent.focus_set()
        self.destroy()

    def ok(self,event=None):
        "event handler for ok button"
        if not self.validate():
            return
        self.withdraw()
        self.update_idletasks()

        self.okTasks()
        #do something here
        
        self.close()


    def validate(self):
        "verify that all data is ok before closing window"
        return 1
    
    def okTasks(self):
        "override to do something when ok is clicked"
        pass

    def cancelTasks(self):
        "override to do something when cancel is clicked"
        pass

class UseBriberyDialog(Dialog):
    "a dialog asking the player if he wants to use a bribery card"
    def __init__(self,parent,companyName, companyColor,useBribery):
        self.useBribery = useBribery
        self.companyName = companyName
        self.companyColor = companyColor
        Dialog.__init__(self,parent,"Use Bribery?")

    def okTasks(self):
        self.useBribery[0] = 1

    def buildBody(self,frame):
        l = Label(frame,text=self.companyName,bg=self.companyColor,
                  fg=TEXT_COLOR,font=COMPANY_NAME_FONT)
        l.grid(row=0,column=0,sticky=W)
        l = Label(frame,text="Use Bribery Card?",font=DEFAULT_FONT)
        l.grid(row=1,column=0,sticky=W)

class AccidentDialog(Dialog):
    "a dialog to alert players that an accident occurred"
    def __init__(self,parent):
        Dialog.__init__(self,parent,"Accident!")

    def buildBody(self,frame):
        l = Label(frame,text="An Accident Has Occurred!",
                  font=DEFAULT_FONT)
        l.pack()

    def addCancelButton(self,box):
        "do nothing; we should not have a cancel button"
        pass

class AboutDialog(Dialog):
    "a dialog to display the about message"
    def __init__(self,parent):
        Dialog.__init__(self,parent,"About Industrial Waste")

    def buildBody(self,frame):
        row = 0
        for line,fontsize in ABOUT_LINES:
            font = ("Helvetica",fontsize)
            l = Label(frame,text=line,font=font)
            l.grid(row=row,column=0,sticky=W)
            row+= 1
            
    def addCancelButton(self,box):
        pass

class ConfirmCardDialog(Dialog):
    "a dialog asking the player to confirm the use of a card"
    def __init__(self,parent,companyName,companyColor,card,callback,
                 allowPass,hasAdvisor,canPlay):
        self.companyName = companyName
        self.companyColor = companyColor
        self.card = card
        self.callback = callback
        self.allowPass = allowPass
        self.hasAdvisor = hasAdvisor
        self.canPlay = canPlay #can this card be played
        Dialog.__init__(self,parent,"Play " + card)

    def okTasks(self):
        cp = game.CardPlay(self.card)
        cp.action = self.option.get()
        cp.useAdvisor = self.advisor.get()
        if self.card == game.CARD_INNOVATION:
            cp.automation = self.innovation[game.AUTOMATION].get()
            cp.rawMaterialUsage = self.innovation[
                game.RAW_MATERIAL_USAGE].get()
            cp.wasteReduction = self.innovation[game.WASTE_REDUCTION].get()
        elif self.card == game.CARD_HIRING_FIRING:
            cp.hiringFiring = self.hiringFiring.get()
            
        self.callback(cp)

    def validate(self):
        useAdvisor = self.advisor.get()
        if self.card == game.CARD_INNOVATION:
            count = 0
            for t in game.ALL_INNOVATION:
                if self.innovation[t].get():
                    count = count + 1
            if useAdvisor:
                if count > 2 or count < 1:
                    return 0
            else:
                if self.option.get() == game.PLAY and count != 1:
                    return 0
        return 1
                
            

    def buildBody(self,frame):
        l = Label(frame,text=self.companyName,bg=self.companyColor,
                  fg=TEXT_COLOR,font=COMPANY_NAME_FONT)
        l.grid(row=0,column=0,sticky=W,columnspan=2)
        #build card use radiobuttons
        leftPane = Frame(frame,relief=RIDGE,borderwidth=2)
        leftPane.grid(column=0,row=1,rowspan=5,sticky=N+W)

        self.option = IntVar()
        row = 1
        if self.canPlay:
            r = Radiobutton(leftPane,text="Play %s" % self.card,
                            font=DEFAULT_FONT,
                            variable=self.option,value=game.PLAY)
            r.grid(row=row,column=0,sticky=W)
            row = row+1

        
        if self.allowPass:
            r = Radiobutton(leftPane,text="Save %s" % self.card,
                            font=DEFAULT_FONT,
                            variable=self.option,value=game.SAVE)
            r.grid(row=row,column=0,sticky=W)
            row=row+1

        if self.card != game.CARD_RAW_MATERIALS:
            r = Radiobutton(leftPane,text="Discard %s" % self.card,
                            font=DEFAULT_FONT,
                            variable=self.option,value=game.DISCARD)
            r.grid(row=row,column=0,sticky=W)
            row = row+1
        

        if self.canPlay:
            self.option.set(game.PLAY)
        elif self.allowPass:
            self.option.set(game.SAVE)
        else:
            self.option.set(game.DISCARD)

        #build option radiobuttons
        rightPane = Frame(frame,relief=RIDGE,borderwidth=2)
        rightPane.grid(column=1,row=1,rowspan=5,sticky=N+W)

        row = 1
        if self.card == game.CARD_INNOVATION:
            self.innovation = {}
            for t in game.ALL_INNOVATION:
                self.innovation[t]= IntVar()
                r = Checkbutton(rightPane,text=t,
                                font=DEFAULT_FONT,
                                variable=self.innovation[t])
                r.grid(row=row,column=1,sticky=W)
                row = row + 1

        elif self.card == game.CARD_HIRING_FIRING:
            self.hiringFiring = IntVar()
            self.hiringFiring.set(game.FIRE)
            r = Radiobutton(rightPane,text="Fire",font=DEFAULT_FONT,
                            variable=self.hiringFiring,value=game.FIRE)
            r.grid(row=row,column=1,sticky=W)
            row = row + 1
            r = Radiobutton(rightPane,text="Hire",font=DEFAULT_FONT,
                            variable=self.hiringFiring,value=game.HIRE)
            r.grid(row=row,column=1,sticky=W)
            row = row + 1

        self.advisor = IntVar()
        self.advisor.set(0)
        if self.hasAdvisor:
            advisorPane = Frame(rightPane,relief=RIDGE,borderwidth=2)
            advisorPane.grid(row=row,column=1,sticky=W+E)
            c = Checkbutton(advisorPane,text="Use Advisor",font=DEFAULT_FONT,
                            variable=self.advisor)
            c.grid(row=0,column=0,sticky=W)
            
            
MAX_PLAYERS=4
MIN_PLAYERS=2
class NewGameDialog(Dialog):
    "a dialog allowing a new game to be setup"
    def __init__(self,parent,ok_callback):
        self.ok_callback = ok_callback
        Dialog.__init__(self,parent,"New Game")        

    def okTasks(self):
        nameList = map(StringVar.get, self.name)
        controlList = map(IntVar.get, self.control)
        self.ok_callback( self.numPlayers.get(),
                          nameList, COMPANY_COLORS,
                          controlList)
    
    def buildBody(self,frame):
        self.numPlayers = IntVar()
        self.numPlayers.set(4)
        self.numPlayersScale = Scale(frame,from_=MIN_PLAYERS,
                                     to=MAX_PLAYERS,
                                     orient=HORIZONTAL,
                                     label="Number of Players",
                                     command=self.setNumPlayers,
                                     variable=self.numPlayers)
        self.numPlayersScale.grid(row=0,column=0,sticky=W)
        self.name = []
        self.nameEntry = []
        self.control = []
        for i in range(MAX_PLAYERS):
            pane = Frame(frame,relief=RIDGE,borderwidth=1)
            pane.grid(row=i+1,column=0)
            
            tv =  StringVar()
            tv.set(DEFAULT_NAMES[i])
            self.name.append(tv)
            ne = Entry(pane,width=20,textvariable=tv)
            self.nameEntry.append(ne)

            Label(pane,text="Company Name").grid(row=i+1,column=0,padx=3)
            ne.grid(row=i+1,column=1,padx=3)

            cv = IntVar()
            if i == 0:
                cv.set(1)
            self.control.append(cv)
            r1 = Radiobutton(pane,text="Human",font=DEFAULT_FONT,
                             variable=cv,value=1)
            r1.grid(row=i+1,column=2,padx=3)
            
            r2 = Radiobutton(pane,text="Computer",font=DEFAULT_FONT,
                             variable=cv,value=0)
            r2.grid(row=i+1,column=3,padx=3)
            
    def setNumPlayers(self,event=None):
        maxIndex = self.numPlayers.get() - 1
        for i in range(len(self.nameEntry)):
            if i > maxIndex:
                self.nameEntry[i].config(state=DISABLED)
                self.nameEntry[i].config(bg="gray")
            else:
                self.nameEntry[i].config(state=NORMAL)
                self.nameEntry[i].config(bg=TEXT_COLOR)


class BidDialog(Dialog):
    "allows current player to places bids for goods"

    def __init__(self,parent, goods,highBidder,highBidderColor,
                 highBid,auctioneerName,
                 auctioneerColor,companyName,companyColor,callback):
        self.goods = goods
        self.highBid = highBid
        self.highBidder = highBidder
        self.highBidderColor = highBidderColor
        self.auctioneerName = auctioneerName
        self.auctioneerColor= auctioneerColor
        self.companyName = companyName
        self.companyColor = companyColor
        self.callback = callback
        Dialog.__init__(self,parent,"Place A Bid","Bid","Pass")

    def okTasks(self):
        self.callback(self.bidAmount)

    def cancelTasks(self):
        self.callback(0)
        
    def validate(self):
        try:
            self.bidAmount = string.atoi(self.bidAmountVar.get())
        except ValueError,e:
            return 0
        return 1
            
    def buildBody(self,frame):
        row = 0
        l = Label(frame,text=self.companyName,bg=self.companyColor,
                  fg=TEXT_COLOR,font=COMPANY_NAME_FONT)
        l.grid(row=row,column=0,columnspan=2,sticky=W)
        row = row + 1

        l = Label(frame,text="%d Goods Auctioned by:" %self.goods,
                  font=DEFAULT_FONT)
        l.grid(row=row,column=0,pady=4)
        l = Label(frame,text=self.auctioneerName,
                  bg=self.auctioneerColor,
                  fg=TEXT_COLOR,font=DEFAULT_FONT)
        l.grid(row=row,column=1,pady=4)
        row = row + 1

        if self.highBid > 0:
            l = Label(frame,text="High Bid %d by:" %self.highBid,
                      font=DEFAULT_FONT)
            l.grid(row=row,column=0,pady=4)
            l = Label(frame,text=self.highBidder,
                      bg=self.highBidderColor,
                      fg=TEXT_COLOR,font=DEFAULT_FONT)
            l.grid(row=row,column=1,pady=4)
            row = row + 1

        
        self.bidAmountVar = StringVar()
        self.bidAmountVar.set(str(self.highBid + 1))
        e = Entry(frame,width=8,textvariable=self.bidAmountVar,
                  font=DEFAULT_FONT)
        e.grid(row=row,column=0,padx=4,pady=1)
        e.selection_range(0,END)
        return e #set focus to bid entry box

class LayoutDialog(Dialog):
    "a dialog to allow users to choose cards from the layout"

    def __init__(self,parent,layout,companyName, companyColor,ok_callback):
        self.layout = layout
        self.okCallback = ok_callback
        self.companyName = companyName
        self.companyColor = companyColor
        self.selected = None
        Dialog.__init__(self,parent,"Card Selection")

    def okTasks(self):
        self.okCallback(self.selected)

    def addCancelButton(self,box):
        "do nothing; we should not have a cancel button"
        pass

    def validate(self):
        if self.selected is None:
            return 0
        return 1
    
    def buildBody(self,frame):
        l = Label(frame,text=self.companyName,bg=self.companyColor,
                  fg=TEXT_COLOR,font=COMPANY_NAME_FONT)
        l.grid(row=0,column=0,columnspan=2,sticky=W)
                  
        self.panes = []
        for i in range(len(self.layout)):
            pane = Frame(frame,relief=RIDGE,borderwidth=1)
            self.panes.append( pane)
            pane.grid(row=1,column=i,rowspan=2)

            cards = self.layout[i]
            for j in range(len(cards)):
                card = cards[j]
                def specificClick(ob=self,paneIndex=i):
                    ob.cardClick(paneIndex)
                b = Button(pane,text=card,width=CARD_WIDTH,
                           font=CARD_FONT,relief=CARD_RELIEF,
                           bg=CARD_BACKGROUND,fg=CARD_FOREGROUND,
                           command=specificClick)
                b.grid(row=j,column=0,padx=10)
                               
    def cardClick(self,paneIndex):
        self.selected = paneIndex
        for i in range(len(self.panes)):
            pane = self.panes[i]
            if i == paneIndex:
                color = CARD_HIGHLIGHT
            else:
                color = CARD_BACKGROUND
            for child in pane.winfo_children():
                child.config(bg=color)
