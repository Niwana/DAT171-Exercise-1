from cardlib import *
from PyQt5.QtCore import *


class DeckModel:
    """ A class representing a standard card deck. It contains functions for creating an empty deck,
        creating the 52 cards and shuffling the deck. """

    def __init__(self):
        super().__init__()
        self.deck = StandardDeck()
        self.deck.create_deck()
        self.deck.shuffle()


class TexasHoldEm(QObject):
    """ A class representing the Texas Hold 'em poker card game. It contains functions for
    initiating the blinds, progressing and restarting the game, showdown and the following
    player actions: call, bet and fold. """

    new_credits = pyqtSignal()
    new_pot = pyqtSignal()
    game_message = pyqtSignal(str)
    game_message_warning = pyqtSignal(str)
    new_output = pyqtSignal(str)

    def __init__(self, players, deck_model, starting_credits):
        super().__init__()
        self.players = players

        # Let the first player begin
        self.active_player = 0
        self.players[0].active = True

        self.starting_credits = starting_credits

        self.deck_model = deck_model

        self.pot = 0
        self.big_blind = self.starting_credits // 100
        self.small_blind = self.big_blind // 2
        self.initiate_blind(self.small_blind + self.big_blind)
        self.previous_bet = self.small_blind
        self.actions = 0

        # Create the community cards view
        self.community_cards = CommunityCards(self.deck_model)

        # Flip the starting player's cards in order to reveal them
        self.players[self.active_player].flip_cards()

    def initiate_blind(self, blinds):
        """ A function for initiating the small and big blind, with the big blind being
        1/100th of the player starting credit. The function subtracts the blinds from the
        respective players' credits. """

        for player in self.players:
            if player.active:
                player.credits -= self.small_blind
            else:
                player.credits -= self.big_blind
        self.pot += blinds
        self.new_pot.emit()

    def call(self):
        """ A player function for calling the preceding player's bet. The function subtracts
        the previous bet from the active player's credits, emits the changes to the view model,
        changes the active player and progresses the game. """

        output_text = "{} called: - ${}".format(self.players[self.active_player].name, self.previous_bet)

        if self.players[self.active_player].credits >= self.previous_bet and not self.previous_bet == 0:
            self.pot += self.previous_bet
            self.new_pot.emit()

            self.players[self.active_player].credits -= self.previous_bet
            self.new_credits.emit()
            self.new_output.emit(output_text)
            self.actions += 1

            self.active_player = (self.active_player + 1) % len(self.players)

            # Update the players to hide their cards when it is not their turn
            for player in self.players:
                player.flip_cards()

            self.progress_game()

        else:
            message = "Player {} won! Not enough money remaining.".format(
                self.players[(self.active_player + 1) % len(self.players)].name)
            self.game_message.emit(message)
            self.restart()

    def bet(self, amount):
        """ A player function for placing bets. The function subtracts the chosen amount from
        the active player's credits, emits the changes to the view model, changes the active
        player and progresses the game. """

        if self.players[self.active_player].credits < self.big_blind:
            message = "Player {} won! Not enough money remaining.".format(self.players[(self.active_player + 1) %
                                                                                       len(self.players)].name)
            self.game_message.emit(message)
            self.restart()
        if self.players[(self.active_player + 1) % len(self.players)].credits < self.big_blind:
            message = "Player {} won! Not enough money remaining.".format(self.players[self.active_player].name)
            self.game_message_warning.emit(message)
            self.restart()

        if amount == 0:
            message = "Raises must be larger than zero!"
            self.game_message_warning.emit(message)

        elif self.previous_bet + amount > self.players[self.active_player].credits:
            message = "Not enough money!"
            self.game_message_warning.emit(message)
        else:
            self.pot += amount
            self.new_pot.emit()

            self.players[self.active_player].credits -= (self.previous_bet + amount)
            self.new_credits.emit()

            output_text = "{} bet ${} and raised ${}".format(self.players[self.active_player].name, self.previous_bet,
                                                             amount)

            self.previous_bet = (self.previous_bet + amount)
            self.actions += 1

            self.new_output.emit(output_text)

            self.active_player = (self.active_player + 1) % len(self.players)

            # Update the players to hide their cards when it is not their turn
            for player in self.players:
                player.flip_cards()

            self.progress_game()

    def fold(self):
        """ A player function for folding. The function emits the changes to the view model,
        changes the active player and starts a new round. """

        self.players[1 - self.active_player].credits += self.pot

        output_text = "{} folded.\n{} is awarded the pot of ${}".format(self.players[self.active_player].name,
                                                                        self.players[(self.active_player + 1)
                                                                                     % len(self.players)].name,
                                                                        self.pot)
        if self.players[self.active_player].credits < self.big_blind:
            message = "Player {} won! Not enough money remaining.".format(self.players[(self.active_player + 1) %
                                                                                       len(self.players)].name)
            self.game_message.emit(message)
            self.restart()
        if self.players[(self.active_player + 1) % len(self.players)].credits < self.big_blind:
            message = "Player {} won! Not enough money remaining.".format(self.players[self.active_player].name)
            self.restart()
            self.game_message.emit(message)
        else:
            self.next_round(succeeds_fold=True)

        self.players[self.active_player].flip_cards()
        self.new_output.emit(output_text)

    def showdown(self):
        """ A function for the showdown after all community cards has been dealt and the
        players have placed their bets. The function compares the poker hands and chooses
        a winner, awards the winning player the pot and emits the changes to the view model. """

        poker_hands = []
        message = ""
        for player in self.players:
            poker_hands.append(player.hand.best_poker_hand(self.community_cards.cards))

            # Reveal all cards when the round is over
            player.reveal_cards()

        if poker_hands[0].type > poker_hands[1].type:
            message = "Player {} won! \nPoker hand >{}< won against >{}<".format(
                self.players[0].name, str(poker_hands[0].type), str(poker_hands[1].type))
            self.players[0].credits += self.pot

        if poker_hands[0].type < poker_hands[1].type:
            message = "Player {} won! \nPoker hand >{}< won against >{}<".format(
                self.players[1].name, str(poker_hands[1].type), str(poker_hands[0].type))
            self.players[1].credits += self.pot

        if poker_hands[0].type == poker_hands[1].type:
            if poker_hands[0].highest_values > poker_hands[1].highest_values:
                message = "Player {} won! \nHighest value >{}< won against >{}<".format(
                    self.players[0].name, str(poker_hands[0].highest_values), str(poker_hands[1].highest_values))
                self.players[0].credits += self.pot

            elif poker_hands[0].highest_values < poker_hands[1].highest_values:
                message = "Player {} won! \nHighest value >{}< won against >{}<".format(
                    self.players[1].name, str(poker_hands[1].highest_values), str(poker_hands[0].highest_values))
                self.players[1].credits += self.pot

            elif poker_hands[0].highest_values == poker_hands[1].highest_values:
                message = "It is a draw! Both players had >{}< and highest value >{}<".format(
                    poker_hands[0].type.name, str(poker_hands[0].highest_values))

                for player in self.players:
                    player.credits += (self.pot // len(self.players))
            else:
                self.game_message_warning.emit("Incorrect comparison of poker hands")

        self.new_output.emit(message)
        self.game_message.emit(message)
        self.new_credits.emit()
        self.new_pot.emit()

    def progress_game(self):
        """ A function for progressing the game after a player has finished their turn.
        The function responds with different scenarios depending on the number of preceding
        turns: it calls the respective functions for dealing the flop, turn, river or initiating
        a showdown. """

        if self.actions == len(self.players):
            # Reveal the 3 first cards
            output_text = "Dealing the flop..."

            self.new_output.emit(output_text)
            self.community_cards.flop()

        if self.actions == 2 * len(self.players):
            # Reveal a 4th card
            output_text = "Dealing the turn..."

            self.new_output.emit(output_text)
            self.community_cards.turn()

        if self.actions == 3 * len(self.players):
            # Reveal a 5th card
            output_text = "Dealing the river..."

            self.new_output.emit(output_text)
            self.community_cards.river()

        if self.actions == 4 * len(self.players):
            self.showdown()

    def restart(self):
        """ A function for restarting the game. The function changes the active player, clears
            the pot, the number of previous actions and the previous bet, creates a new deck and
            deals new hole cards to the players and emits all changes to the view model. """

        self.pot = 0
        self.actions = 0
        self.previous_bet = self.small_blind
        self.initiate_blind(self.small_blind + self.big_blind)

        for player in self.players:
            player.credits = self.starting_credits

        # Let the first player begin
        self.active_player = (self.active_player + 1) % len(self.players)
        self.players[self.active_player].active = True

        self.players[self.active_player - 1].flip_cards()
        self.community_cards.flip_cards()

        self.deck_model = DeckModel()

        for player in self.players:
            player.new_cards(self.deck_model)

        output_text = "Starting game...\n{} post the big blind [${}]\n{} post the small blind [${}]".format(
            self.players[(self.active_player + 1) % len(self.players)].name, self.big_blind,
            self.players[self.active_player].name, self.small_blind)

        message = "Player {} won!".format(self.players[1].name)
        self.game_message.emit(message)

        self.new_pot.emit()
        self.new_credits.emit()
        self.new_output.emit(output_text)

    def next_round(self, succeeds_fold=False):
        """ A function for initiating the next round. The function changes the active player, clears
            the pot and the number of previous actions, creates a new deck and deals new hole cards
            to the players and emits all changes to the view model. """

        self.pot = 0
        self.actions = 0
        self.previous_bet = self.small_blind
        self.initiate_blind(self.small_blind + self.big_blind)

        # Let the first player begin
        self.active_player = (self.active_player + 1) % len(self.players)
        self.players[self.active_player].active = True

        self.players[self.active_player-1].flip_cards()

        if not succeeds_fold:
            self.community_cards.flip_cards()
        if succeeds_fold:
            self.community_cards.flip_all_cards()

        # Create a new deck
        self.deck_model = DeckModel()

        # Creates new cards
        self.community_cards.new_cards(self.deck_model)
        for player in self.players:
            player.new_cards(self.deck_model)

        output_text = "Initiating round.\n{} post the big blind [${}]\n{} post the small blind [${}]".format(
            self.players[(self.active_player + 1) % len(self.players)].name, self.big_blind,
            self.players[self.active_player].name, self.small_blind)

        self.new_pot.emit()
        self.new_credits.emit()
        self.new_output.emit(output_text)


def convert_card_names(hand):
    """ A simple function for translating the cards into a corresponding format for the .svg
    image files that visualize the cards on screen."""

    cards = []
    for i, color in enumerate('CDSH'):
        for card in hand:
            if card.get_suit() == i and card.get_value() < 11:
                cards.append('{}{}'.format(card.get_value(), color))
            if card.get_suit() == i and card.get_value() == 11:
                cards.append('{}{}'.format('J', color))
            if card.get_suit() == i and card.get_value() == 12:
                cards.append('{}{}'.format('Q', color))
            if card.get_suit() == i and card.get_value() == 13:
                cards.append('{}{}'.format('K', color))
            if card.get_suit() == i and card.get_value() == 14:
                cards.append('{}{}'.format('A', color))
    return cards


class Player(QObject):
    """ A class representing the player with its' attached name, credit, cards and status as
    an active player. It contains functions for flipping and revealing the cards."""

    update_cards_data = pyqtSignal()

    def __init__(self, player_name, deck_model, starting_credits=50000):
        super().__init__()
        self.name = player_name
        self.credits = starting_credits
        self.active = False
        self.deck = deck_model.deck

        # Create the hand
        self.cards = deck_model.deck.draw_card(2)
        self.hand = Hand()

        for card in self.cards:
            self.hand.add_card(card)

        self.cards_to_view = convert_card_names(self.cards)

        self.flipped_cards = [True] * len(self.cards)

    def new_cards(self, deck_model):
        self.cards = deck_model.deck.draw_card(2)

        self.hand.remove_card([0, 1])
        for card in self.cards:
            self.hand.add_card(card)

        self.cards_to_view = convert_card_names(self.cards)
        self.update_cards_data.emit()

    def flip_cards(self):
        self.flipped_cards = [not i for i in self.flipped_cards]
        self.update_cards_data.emit()

    def reveal_cards(self):
        self.flipped_cards = [False] * len(self.cards)
        self.update_cards_data.emit()


class CommunityCards(QObject):
    """ A class representing the community cards. It contains functions for dealing the
    flop, turn and river. """

    update_cards_data = pyqtSignal()

    def __init__(self, deck_model):
        super().__init__()
        super().__init__()
        self.deck = deck_model.deck
        self.cards = self.deck.draw_card(5)
        self.cards_to_view = convert_card_names(self.cards)

        # Start with 0 cards revealed
        self.flipped_cards = [True] * len(self.cards)

        self.update_cards_data.emit()

    def new_cards(self, deck_model):
        self.cards = deck_model.deck.draw_card(5)
        self.cards_to_view = convert_card_names(self.cards)
        self.update_cards_data.emit()

    def flip_cards(self):
        self.flipped_cards = [not i for i in self.flipped_cards]
        self.update_cards_data.emit()

    def flip_all_cards(self):
        self.flipped_cards = [True] * len(self.cards)
        self.update_cards_data.emit()

    def flop(self):
        for i in range(len(self.cards) - 2):
            self.flipped_cards[i] = False

        self.update_cards_data.emit()

    def turn(self):
        for i in range(len(self.cards) - 1):
            self.flipped_cards[i] = False

        self.update_cards_data.emit()

    def river(self):
        for i in range(len(self.cards)):
            self.flipped_cards[i] = False

        self.update_cards_data.emit()
