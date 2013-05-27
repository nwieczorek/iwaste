import game
import random

def log(msg):
    print "<ai>",msg

class SimpleAI:
    def __init__(self,gameState):
        self.gameState = gameState

        
    def getCardPlay(self):
        "return a card play for the current company"
        company = self.gameState.getCurrent()
        self.company = company
        self.evaluations = []
        if game.CARD_ADVISOR in company.cards:
            advisorRange = (0,1)
        else:
            advisorRange = (0,)
        actions = [game.PLAY,game.DISCARD]
        if len(company.cards) == 1:
            actions.append(game.SAVE)

        #go through all possible plays
        for c in company.cards:
            for a in actions:
                if c == game.CARD_RAW_MATERIALS and a == game.DISCARD:
                    continue
                
                if c == game.CARD_ADVISOR:
                    p = game.CardPlay(c)
                    p.action = a
                    self.addEvaluation(p)
                else:
                    for adv in advisorRange:
                        if c == game.CARD_INNOVATION:
                            for i in game.ALL_INNOVATION:
                                p = game.CardPlay(c)
                                p.action = a
                                p.useAdvisor = adv
                                p.setInnovation(i)
                                self.addEvaluation(p)
                        elif c == game.CARD_HIRING_FIRING:
                            for h in (game.HIRE,game.FIRE):
                                p = game.CardPlay(c)
                                p.action = a
                                p.useAdvisor = adv
                                p.hiringFiring = h
                                self.addEvaluation(p)
                        else:
                            p = game.CardPlay(c)
                            p.action = a
                            p.useAdvisor = adv
                            self.addEvaluation(p)

        play = self.getBestPlay()
        return play


    def addEvaluation(self,play,otherCards=[],bonus=0):
        "add a value,play pair to the evaluations list"
        val = self.evaluatePlay(play,otherCards) + bonus
        self.evaluations.append( (val,play))

    def getBestPlay(self):
        "sort the plays by value and return the last (highest valued)"
        self.evaluations.sort()
        play = self.evaluations[len(self.evaluations)-1][1]
        return play


    def getStackValue(self):
        "sum the best valued plays for each card type in the stack"
        values = {}
        for val,play in self.evaluations:
            if values.has_key(play.card):
                if val > values[play.card]:
                    values[play.card] = val
            else:
                values[play.card] = val
        sum = 0
        for k in values.keys():
            sum = sum + values[k]
        return sum


    def useBribery(self):
        "always use bribery if we have it"
        return 1

        
    def evaluatePlay(self,play,otherCards):
        "get a value for this play"
        company = self.company
        val = 0

        if play.card == game.CARD_ORDER:
            if play.action == game.PLAY:
                if company.canDoOrder():
                    if company.waste > game.MAX_YELLOW:
                        val = 30
                    elif company.waste > game.MAX_GREEN:
                        val = 55                        
                    else:
                        val = 75

                    if company.money < (company.workers + 5):
                        val += 25
                    if play.useAdvisor:
                        val += 10
            
        elif play.card == game.CARD_RAW_MATERIALS:
            if play.action == game.PLAY:
                if company.canDoOrder():
                    val = 40
                else:
                    val = 70
                if play.useAdvisor:
                    val += 15
        elif play.card == game.CARD_GROWTH:
            if play.action == game.PLAY:
                if (   ((company.growth == (game.MAX_GROWTH - 1)) or
                       ((company.growth >= (game.MAX_GROWTH - 2) and
                         play.useAdvisor))) and
                       not company in self.gameState.getWinners()):
                    val = -10
                elif game.CARD_ORDER in company.cards and \
                   company.canDoOrder():
                    val = 90
                else:
                    val = 70
                if play.useAdvisor:
                    val += 5
                        
        elif play.card == game.CARD_INNOVATION:
            if play.action == game.PLAY:
                if play.automation and \
                   company.automation > game.MIN_TECH:
                    val = 35
                    if (game.CARD_HIRING_FIRING in company.cards) or \
                       (game.CARD_HIRING_FIRING in otherCards):
                        val += 5
                    val += ((game.MAX_TECH - company.automation) * 3)
                elif play.rawMaterialUsage and \
                     company.rawMaterialUsage > game.MIN_TECH:
                    val = 40
                    val += ((game.MAX_TECH - company.rawMaterialUsage) * 3)
                elif play.wasteReduction and \
                     company.wasteReduction > game.MIN_TECH:
                    val = 40
                    val += ((game.MAX_TECH - company.wasteReduction) * 3)
                if (  (company.money >= (5 + company.workers)) or 
                      (  (game.CARD_ORDER in company.cards or
                         game.CARD_ORDER in otherCards) and
                         company.canDoOrder() and
                         company.money >= 5)  ):
                    val = val + 45
                if play.useAdvisor and company.money >= (10 + company.workers):
                    val = val + 20
                    
        elif play.card == game.CARD_HIRING_FIRING:
            if play.action == game.PLAY:
                if company.automation < company.workers and \
                   play.hiringFiring == game.FIRE:
                    val = 70
                elif company.automation > company.workers and \
                     play.hiringFiring == game.HIRE and \
                     (game.CARD_INNOVATION not in company.cards or
                      game.CARD_INNOVATION not in otherCards):
                    val = 80
                if play.useAdvisor:
                    val -= 20
        elif play.card == game.CARD_WASTE_DISPOSAL:
            if play.action == game.PLAY:
                if company.waste > game.MAX_YELLOW:
                    val = 100
                elif company.waste > game.MAX_GREEN:
                    val = 70
                elif company.waste > 2:
                    val = 40
                if play.useAdvisor:
                    if company.waste > game.MAX_GREEN:
                        val += 10
                    
        elif play.card == game.CARD_WASTE_REMOVAL:
            if play.action == game.PLAY:
                if company.waste > game.MAX_YELLOW:
                    val = 90
                elif company.waste > game.MAX_GREEN:
                    val = 60
                else:
                    val = 30
                if play.useAdvisor:
                    val += 10
        elif play.card == game.CARD_ADVISOR:
            if play.action == game.PLAY:
                if company.loans > 0:
                    if company.money >= 10:
                        val = 30
                        if company.money >= 15 or \
                           (game.CARD_ORDER in company.cards and 
                            company.canDoOrder()):
                            val += 90


        if play.action == game.SAVE:
            val = 10

        val = val + random.choice(range(10))
        log("value of " + play.card + ":" + str(val))
        return val


    def getBid(self):
        "return a bid for the current auction"
        company = self.gameState.getCurrent()
        highBid = self.gameState.highBid
        goods = self.gameState.auctionGoods
        bid = 0

        goodValue = (company.growth / float(company.rawMaterialUsage + 1))
        goodsValue = goodValue * goods

        if company.rawMaterials >= (company.rawMaterialUsage * 2):
            need = 0.3
        elif company.rawMaterials >= company.rawMaterialUsage:
            need = 0.6
        else:
            need = 1

        log("goods value:" + str(goodsValue) + ", need:" + str(need))
        bid = min(company.money,int( goodsValue * need))

        #lower the bid if we cannot afford our workers
        if not game.CARD_ORDER in company.cards:
            if (company.money - bid) < company.workers:
                bid = max(0,company.money - company.workers)
        
        #add some money to the bid if we have lots
        if company.money > 30:
            bid += ((company.money - 20) / 5)

        #check to see if we are the last bidder
        if self.gameState.bids == self.gameState.num_companies  and \
           bid > highBid:
            bid = highBid + 1

        #check to see if we are in the final round
        if self.gameState.isGameOver():
            if not (game.CARD_ORDER in company.cards and 
                    company.rawMaterials + goods >= company.rawMaterialUsage):
                bid = 0
        
        if bid < highBid:
            bid = 0
        return bid

    def chooseCardStack(self):
        "choose a stack of cards from the layout"
        company = self.gameState.getCurrent()
        self.company = company
        layout = self.gameState.layout
        bestIndex = 0
        bestValue = 0
        for i in range(len(layout)):
            stack = layout[i]
            self.evaluations = []
            for card in stack:
                if card == game.CARD_INNOVATION:
                    for inn in game.ALL_INNOVATION:
                        p = game.CardPlay(card)
                        p.setInnovation(inn)
                        self.addEvaluation(p,stack)
                elif card == game.CARD_HIRING_FIRING:
                    for hf in (game.HIRE,game.FIRE):
                        p = game.CardPlay(card)
                        p.hiringFiring = hf
                        self.addEvaluation(p,stack)
                elif card == game.CARD_ADVISOR:
                    p = game.CardPlay(card)
                    self.addEvaluation(p,stack,80)
                elif card == game.CARD_BRIBERY:
                    p = game.CardPlay(card)
                    p.action = game.SAVE
                    if company.waste <= game.MAX_GREEN:
                        bonus = 10
                    elif company.waste <= game.MAX_YELLOW:
                        bonus = 50
                    else:
                        bonus = 80
                    self.addEvaluation(p,stack,bonus)
                else:
                    p = game.CardPlay(card)
                    self.addEvaluation(p,stack)

            val = self.getStackValue()
            log("value of stack " + str(stack) + " is " + str(val))
            if val > bestValue:
                bestValue = val
                bestIndex = i

                
        return bestIndex
                
            

        
        
        
