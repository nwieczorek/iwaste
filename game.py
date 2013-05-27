import random
import copy

#some constants
MIN_GROWTH=14
MAX_GROWTH=20
MIN_WORKERS=1
MAX_WORKERS=5

MAX_TECH=5
MIN_TECH=1

START_MONEY=15
START_RAW_MATERIALS=5
    
MIN_WASTE=0
MAX_WASTE=16
MAX_GREEN=8
MAX_YELLOW=12

HIRE=1
FIRE=-1
#innovation types
AUTOMATION="Rationalization"
RAW_MATERIAL_USAGE="Raw Material Usage"
WASTE_REDUCTION="Waste Reduction"
ALL_INNOVATION =(AUTOMATION,RAW_MATERIAL_USAGE, WASTE_REDUCTION)

#card types
CARD_ORDER="Order"
CARD_RAW_MATERIALS="Raw Materials"
CARD_GROWTH="Growth"
CARD_INNOVATION="Innovation"
CARD_WASTE_DISPOSAL="Waste Disposal"
CARD_ADVISOR="Advisor"
CARD_HIRING_FIRING="Hiring/Firing"
CARD_WASTE_REMOVAL="Waste Removal"
CARD_BRIBERY="Bribery"
CARD_ACCIDENT="Accident"
PASS="pass"

#card actions
PLAY=1
DISCARD=2
SAVE=3
ALL_ACTIONS=(PLAY,DISCARD,SAVE)
#GAME_PHASES
PHASE_NEW_ROUND="new round"
PHASE_CARD_DRAFT="card draft"
PHASE_ACCIDENT="accident"
PHASE_CARD_PLAY="card play"
PHASE_AUCTION="auction"
PHASE_BASIC_COSTS="basic costs"
PHASE_GAME_OVER="game over"

#scoring
INNOVATION_SCORING = { 5:1, 4:3, 3:6, 2:10,1:15}

def log(msg):
    print "<game>",msg

class Game:
    "used to handle all data for the game"

    def __init__(self, num_companies):
        self.num_companies = num_companies
        self.companies = []
        for i in range(self.num_companies):
            self.companies.append( Company(i))

        self.deck = Deck()
        self.gameOver = 0
        self.start = 0
        self.current = 0
        self.passes = 0
        self.payouts = 0

    def newGame(self):
        self.start = random.choice( range(self.num_companies))
        self.current = self.start

    def copy(self):
        "return a copy of the game state"
        return copy.deepcopy(self)
        #the copy will not have an identical deck or start player
        #c = Game(0)
        #c.num_companies = self.num_companies
        #for company in self.companies:
        #    c.companies.append( company.copy())
        #return c

    def newRound(self):
        "begin a new round"
        log("new round")
        self.passes = 0
        self.payouts = 0
        self.layout = self.deck.deal(self.num_companies)
        self.phase = PHASE_NEW_ROUND

        #rotate start player
        self.start = (self.start + 1) % self.num_companies
        self.current = self.start


    def anyVulnerable(self):
        "are there any companies vulnerable to accidents"
        for c in self.companies:
            if c.isVulnerable():
                return 1
        return 0

    def handleAccident(self,useBribery=0):
        "handle an accident for the current company"
        company = self.getCurrent()
        fine,shrink = company.getPenalties(useBribery)
        if useBribery:
            self.discard(company,CARD_BRIBERY)

        company.growth = max(MIN_GROWTH,company.growth - shrink)
        while company.money < fine:
            company.takeLoan()

        company.money = company.money - fine

        self.next()


    def getCurrent(self):
        "return the current company"
        return self.companies[self.current]

    def chooseLayout(self,index):
        "choose a stack of cards from the layout for the current player"
        cards = self.layout[index]
        self.layout.remove(cards)
        self.companies[self.current].cards.extend(cards)

        self.next()
        return cards

    def next(self,action=PLAY):
        "advance to the next player"
        if action == PASS:
            self.passes = self.passes + 1
        else:
            self.passes =  0
        #print "passes:",self.passes
        if self.phase == PHASE_AUCTION:
            self.bids = self.bids + 1

        if self.phase == PHASE_BASIC_COSTS:
            self.payouts = self.payouts + 1
            
        self.current = (self.current + 1) % self.num_companies
        if self.phase == PHASE_AUCTION:

            if self.bids > self.num_companies:
                self.endAuction()
                self.nextPhase()
        elif self.phase == PHASE_BASIC_COSTS:
            if self.payouts >= self.num_companies:
                self.nextPhase()
        elif self.phase == PHASE_CARD_PLAY:
            if self.passes >= self.num_companies:
                self.nextPhase()
        else:
            if self.current == self.start:
                self.nextPhase()

        if self.phase == PHASE_CARD_PLAY and \
           len(self.getCurrent().cards) == 0:
            self.next(PASS)
                    


    def nextPhase(self):
        "advance to the next game phase"
        if self.phase == PHASE_NEW_ROUND:
            if self.deck.accident or self.gameOver:
                self.phase = PHASE_ACCIDENT
            else:
                self.phase = PHASE_CARD_DRAFT
            
        elif self.phase == PHASE_ACCIDENT:
            if self.gameOver:
                self.phase = PHASE_GAME_OVER
            else:
                self.phase = PHASE_CARD_DRAFT
        elif self.phase == PHASE_CARD_DRAFT:
            self.discardLayout()
            self.phase = PHASE_CARD_PLAY
            self.passes=0
        elif self.phase == PHASE_AUCTION:
            self.phase = PHASE_CARD_PLAY
        elif self.phase == PHASE_CARD_PLAY:
            self.phase = PHASE_BASIC_COSTS
        elif self.phase == PHASE_BASIC_COSTS:
            if self.isGameOver():
                self.gameOver = 1
            self.newRound()
        log("phase is " + self.phase)

    def payBasicCosts(self):
        "pay basic costs for the current company"
        c = self.getCurrent()
        c.payBasicCosts()
        self.next()

    def isGameOver(self):
        "has one of the companies reached maximum growth"
        for c in self.companies:
            if c.growth == MAX_GROWTH:
                return 1
        return 0

    def playPass(self):
        "current player passes"
        self.next(PASS)

    def discardCard(self,card):
        "discard a card and advance turn sequence"
        company = self.getCurrent()
        self.discard(company,card)
        self.next(DISCARD)

    def discardLayout(self):
        "discard the remaining cards in the layout"
        for stack in self.layout:
            for card in stack:
                self.deck.discard(card)        
    
    def discard(self,company,card):
        "discard a card"
        #log("discarding " + card + " from company " + str(company.id))
        company.cards.remove(card)
        self.deck.discard(card)

    def startAuction(self,useAdvisor):
        "do an auction for raw materials"
        log("start auction")
        self.bids = 0
        self.highBid = 0
        self.highBidder = None
        self.auctioneer = self.current
        self.auctionGoods = self.getCurrent().rawMaterialUsage
        if useAdvisor:
            self.auctionGoods = self.auctionGoods * 2
        self.phase = PHASE_AUCTION

    def bid(self,bid):
        "place a bid"
        log("bidding " + str(bid) + " bids: " + str(self.bids))
        if bid > self.highBid:
            self.highBid = bid
            self.highBidder = self.getCurrent()

            while self.highBidder.money < bid:
                self.highBidder.takeLoan()
            
        self.next()
        
    def endAuction(self):
        "complete an auction"
        log("end auction")
        if self.highBid > 0:
            self.highBidder.rawMaterials = self.highBidder.rawMaterials + \
                                           self.auctionGoods
            while self.highBidder.money < self.highBid:
                self.highBidder.takeLoan()
            self.highBidder.money = self.highBidder.money - self.highBid
            auctioneer = self.companies[self.auctioneer]
            if self.highBidder is not auctioneer:
                auctioneer.money = auctioneer.money + self.highBid
            
        
    def playCard(self,cardPlay):
        "have the current company play a card"
        company = self.getCurrent()
        card = cardPlay.card
        self.discard(company,card)

        if cardPlay.useAdvisor:
            self.discard(company,CARD_ADVISOR)
        
        if card == CARD_GROWTH:
            company.doGrowth(cardPlay.useAdvisor)
        elif card == CARD_ORDER:
            company.doOrder(cardPlay.useAdvisor)
        elif card == CARD_WASTE_DISPOSAL:
            company.doWasteDisposal(cardPlay.useAdvisor)
        elif card == CARD_WASTE_REMOVAL:
            if cardPlay.useAdvisor:
                amount = 2
            else:
                amount = 1
            company.waste = max(company.waste - amount,MIN_WASTE)
            for other in self.companies:
                if other == company:
                    continue
                other.waste = min(other.waste + amount, MAX_WASTE)
        elif card == CARD_RAW_MATERIALS:
            self.startAuction(cardPlay.useAdvisor)
        elif card == CARD_HIRING_FIRING:
            company.doHiringFiring(cardPlay)
                
        elif card == CARD_INNOVATION:
            company.doInnovation(cardPlay)

        elif card == CARD_ADVISOR:
            company.payOffLoan()

        self.next(PLAY)

    def getWinners(self):
        "return a list of winners"
        winners = []
        maxScore = 0
        for c in self.companies:
            score = c.getScore()
            if score[0] > maxScore:
                maxScore = score[0]
                winners = []
                winners.append(c)
            elif score == maxScore:
                winners.append(c)
        return winners
            
class CardPlay:
    "Used to represent a single play of cards"

    def __init__(self,card):
        self.card = card
        self.useAdvisor = 0
        self.hiringFiring = 0
        self.automation = 0
        self.rawMaterialUsage = 0
        self.wasteReduction = 0
        self.action = PLAY
        
    def getNumInnovation(self):
        "get the number of increases"
        return self.automation + self.rawMaterialUsage + self.wasteReduction

    def setInnovation(self,innovation):
        if innovation == AUTOMATION:
            self.automation = 1
        elif innovation == RAW_MATERIAL_USAGE:
            self.rawMaterialUsage = 1
        elif innovation == WASTE_REDUCTION:
            self.wasteReduction = 1
            

class Deck:
    "represents the deck of cards in the game"
    def __init__(self):
        self.cards = []
        self.cards.extend( [CARD_ORDER] * 9)
        self.cards.extend( [CARD_RAW_MATERIALS] * 8)
        self.cards.extend( [CARD_GROWTH] * 8)
        self.cards.extend( [CARD_INNOVATION] * 7)
        self.cards.extend( [CARD_WASTE_DISPOSAL] * 7)
        self.cards.extend( [CARD_ADVISOR] * 4)
        self.cards.extend( [CARD_HIRING_FIRING] * 4)
        self.cards.extend( [CARD_WASTE_REMOVAL] * 3)
        self.cards.extend( [CARD_BRIBERY] * 2)
        self.cards.extend( [CARD_ACCIDENT] * 1)

        self.discards=[]

        self.layoutSoFar=[]
        self.accident=0

    def discard(self,card):
        "add a card to the discard pile"
        self.discards.append(card)
        log("discarding %s discard count: %d" % (card,len(self.discards)))
        
    def deal(self,num_players):
        "lay out the card combinations--returns a list of 3 card lists"
        log("dealing")
        layout = []
        self.layoutSoFar = []
        self.accident=0        
        log("pre deal cards: %d  discards: %d  total: %d" %
            (len(self.cards),len(self.discards),
             len(self.cards) + len(self.discards)))
        for i in range(num_players + 1):
            stack = []

            cards_added=0
            while cards_added < 3:
                if len(self.cards) <= 0:
                    log("shuffling in discards")
                    self.cards = self.discards
                    self.discards = []
                c = random.choice( self.cards)
                self.cards.remove(c)

                if c == CARD_ACCIDENT:
                    log("accident card drawn")
                    self.discards.append(c)
                    self.accident=1
                    self.layoutSoFar=layout[:]
                    if cards_added > 0:
                        self.layoutSoFar.append(stack)
                elif c in stack:
                    log("discarding " + c + " already in stack")
                    self.discards.append(c)
                else:
                    stack.append(c)
                    cards_added = cards_added + 1
            layout.append(stack)

        log("post deal cards: %d  discards: %d  total: %d" %
            (len(self.cards),len(self.discards),
             len(self.cards) + len(self.discards)))
        return layout

    
                 
class Company:
    "Holds all data for a single company/player"

    def __init__(self,id):
        self.id = id
        self.growth = MIN_GROWTH
        self.workers = MAX_WORKERS

        self.automation = MAX_TECH
        self.rawMaterialUsage = MAX_TECH
        self.wasteReduction = MAX_TECH
        self.waste = MIN_WASTE
        self.rawMaterials = START_RAW_MATERIALS

        self.money = START_MONEY
        self.loans = 0

        self.cards = []

    def copy(self):
        "return a copy of the company"
        return copy.deepcopy(self)
        

    def takeLoan(self):
        "take out a loan for this company"
        log("%d taking loan" % self.id)
        self.loans = self.loans + 1
        self.money = self.money + 10


    def payOffLoan(self):
        "pay off a loan"
        if self.money >= 10:
            self.money = self.money - 10
            self.loans = max(self.loans - 1,0)

    def canPayOffLoan(self):
        return self.money >= 10 and self.loans > 0

    def getBasicCosts(self):
        return self.workers
    
    def payBasicCosts(self):
        "pay basic costs"
        while self.money < self.workers:
            self.takeLoan()
        self.money = self.money - self.workers


    def canPlay(self,card):
        "can this company play the card"
        return not (
            (card == CARD_ORDER and not self.canDoOrder()) or
            card == CARD_BRIBERY or
            (card == CARD_ADVISOR and not self.canPayOffLoan()))
        

        
    def canDoOrder(self):
        "return true is this company has the resources to do an order"
        if self.workers < self.automation:
            return 0
        if self.rawMaterials < self.rawMaterialUsage:
            return 0
        if (self.waste +self.wasteReduction) > MAX_WASTE:
            return 0
        return 1

    def doOrder(self,useAdvisor):
        "use an order card;  assumes the company has enough materials " \
             "and workers"
        if self.rawMaterials < self.rawMaterialUsage:
            return
        if useAdvisor:
            bonus = 5
        else:
            bonus = 0
        self.rawMaterials = self.rawMaterials - self.rawMaterialUsage
        self.waste = min(self.waste + self.wasteReduction,MAX_WASTE)
        self.money = self.money + self.growth + bonus

    def doGrowth(self,useAdvisor):
        "use a growth card"
        if useAdvisor:
            increment = 2
        else:
            increment = 1
        self.growth = min(MAX_GROWTH, self.growth+increment)

    def doHiringFiring(self, cardPlay):
        "use a hiring/firing card"
        if cardPlay.useAdvisor:
            increment = cardPlay.hiringFiring * 2
        else:
            increment = cardPlay.hiringFiring
        self.workers = max(min(self.workers + increment,MAX_WORKERS),
                           MIN_WORKERS)

    def doWasteDisposal(self,useAdvisor):
        "use a waste disposal card"
        if useAdvisor:
            decrement = 6
        else:
            decrement = 3
        log("waste disposal: " + str(decrement))
        self.waste = max(self.waste - decrement,0)



    def doInnovation(self,cardPlay):
        "use an innovation card"

        if cardPlay.useAdvisor and cardPlay.getNumInnovation() == 1:
            increment = 2
        else:
            increment = 1
        
        if cardPlay.automation:
            self.automation = max(self.automation - increment, MIN_TECH)
        if cardPlay.rawMaterialUsage:
            self.rawMaterialUsage = max(self.rawMaterialUsage - increment,
                                        MIN_TECH)
        if cardPlay.wasteReduction:
            self.wasteReduction = max(self.wasteReduction - increment,
                                      MIN_TECH)

        cost = 5
        if cardPlay.useAdvisor:
            cost = cost * 2
        if self.money < cost:
            self.takeLoan()
        self.money = self.money - cost


    def getPenalties(self,useBribery):
        "get the amount of an accident fine and shrink"
        if self.waste <= MAX_GREEN: # in the green
            fine = 0
            shrink = 0
        elif self.waste <= MAX_YELLOW: # in the yellow
            fine = 5
            shrink = 1
        else: #in the red
            fine = 10
            shrink = 2

        if fine > 0 and useBribery:
            fine = fine + 1
            shrink = 0
        return (fine,shrink)

    def hasBribery(self):
        "does the company have a bribery card"
        return CARD_BRIBERY in self.cards
    
    def isVulnerable(self):
        "is the company vulnerable to an accident"
        if self.waste > MAX_GREEN:
            return 1
        return 0
        
    def getScore(self):
        "calculate the score for this company"
        innovation = INNOVATION_SCORING[self.automation] + \
                     INNOVATION_SCORING[self.rawMaterialUsage] + \
                     INNOVATION_SCORING[self.wasteReduction]
        money = self.money / 2
        loans = self.loans * -10
                     
        total = self.growth + innovation + money  + loans

        return (total,self.growth, innovation, money, loans)

        
    

if __name__ == "__main__":
    #d = Deck()
    #lo = d.deal(2)
    #print lo
    c = Company(23)

    print "%d %d %d %d %d" % c.getScore()

    c.cards.append(CARD_ORDER)
    c.cards.append(CARD_BRIBERY)
    print c.cards
    c2 = c.copy()
    print c2.cards
