import sys
import model
from PyQt5.QtSvg import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


# TODO: lägg till bet, check, call?

# Låt vinsten vara en funktion med potten som input. Kom ihåg att lägga till signals.
# g.player[0].win_money(pot)
# Använd ej följande:
# g.player[0].money += pot

qt_app = QApplication(sys.argv)


class CardItem(QGraphicsSvgItem):
    """ A simple overloaded QGraphicsSvgItem that also stores the card position """
    def __init__(self, renderer, position):
        super().__init__()
        self.setSharedRenderer(renderer)
        self.position = position


class CardView(QGraphicsView):
    def read_cards():
        """

        :return:
        """
        all_cards = dict()
        for suit in 'HDSC':
            for value in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']:
                file = value + suit
                all_cards[file] = QSvgRenderer('cards/' + file + '.svg')
        return all_cards

    back_card = QSvgRenderer('cards/Red_Back_2.svg')
    all_cards = read_cards()

    def __init__(self, player, card_spacing=250, padding=2):
        self.scene = QGraphicsScene()
        super().__init__(self.scene)

        self.card_spacing = card_spacing
        self.padding = padding

        self.player = player

        self.change_cards()

    def change_cards(self):
        self.scene.clear()
        for i, card_ref in enumerate(self.player.cards):
            renderer = self.all_cards[card_ref]
            card = CardItem(renderer, i)
            self.scene.addItem(card)

        self.update_view()

    def update_view(self):
        for card in self.scene.items():
            card_height = card.boundingRect().bottom()
            card_width = card.boundingRect().right()

            scale = (self.height()-2*self.padding) / card_height
            scale_width = (self.width()-2*self.padding) / card_width / len(self.scene.items())

            #card.setPos((self.width() - (self.card_spacing * len(self.scene.items()) / 2)) + card.position * self.card_spacing * scale, 0)
            card.setPos(card.position * self.card_spacing * scale, 0)

            #card.setPos(card.position * self.card_spacing * scale, 0)
            card.setScale(scale)

        self.scene.setSceneRect(-self.padding, -self.padding, self.viewport().width(), self.viewport().height())

    def resizeEvent(self, painter):
        self.update_view()
        super().resizeEvent(painter)





class OtherPlayer(QGroupBox):
    """ The inactive player """
    def __init__(self):
        super().__init__("Other player")

        font = QFont()
        font.setPointSize(20)

        remaining = QLabel(self)
        remaining.setText('Remaining money: 500')
        remaining.setAlignment(Qt.AlignCenter)

        player_name = QLabel(self)
        player_name.setText('Player 2')
        player_name.setMargin(20)
        player_name.setFont(font)
        player_name.setAlignment(Qt.AlignCenter)

        card1 = QLabel(self)
        card1_pixmap = QPixmap('cards\\Red_Back_2.svg')
        smaller_card1 = card1_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.FastTransformation)
        card1.setPixmap(smaller_card1)
        card1.setAlignment(Qt.AlignCenter)

        card2 = QLabel(self)
        card2_pixmap = QPixmap('cards\\Red_Back_2.svg')
        smaller_card2 = card2_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.FastTransformation)
        card2.setPixmap(smaller_card2)
        card2.setAlignment(Qt.AlignCenter)

        empty = QLabel(self)

        hbox = QHBoxLayout()
        hbox.addWidget(empty)
        hbox.addWidget(card1)
        hbox.addWidget(card2)
        hbox.addWidget(remaining)

        hbox_name = QHBoxLayout()
        hbox_name.addWidget(player_name)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox_name)

        self.setLayout(vbox)
        self.setStyleSheet("background-image: url(cards/table.png)")


class CommunityCards(QGroupBox):
    """ Community cards """
    def __init__(self):
        super().__init__("Community cards")

        font = QFont()
        font.setPointSize(20)

        pot = QLabel(self)
        pot.setText('Pot 1000')
        pot.setMargin(20)
        pot.setFont(font)
        pot.setAlignment(Qt.AlignCenter)

        hbox = QHBoxLayout()
        hbox.addWidget(community_card_view)

        hbox_pot = QHBoxLayout()
        hbox_pot.addWidget(pot)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox_pot)

        self.setLayout(vbox)
        self.setStyleSheet("background-image: url(cards/table.png)")


class InputBoxLayout(QGroupBox):
    """ Input box with buttons for call, fold and raise. """

    def __init__(self, game_model):
        super().__init__("Input box")

        # Buttons
        call_button = QPushButton('Call')
        self.raise_button_field = QLineEdit(self)
        raise_button = QPushButton('Raise')
        fold_button = QPushButton('Fold')

        #call_button.clicked.connect(model.buttons.print_click)
        raise_button.clicked.connect(self.print_raise)

        hbox_raise = QHBoxLayout()
        hbox_raise.addWidget(self.raise_button_field)
        hbox_raise.addWidget(raise_button)

        vbox_buttons = QVBoxLayout()
        vbox_buttons.addWidget(call_button)
        vbox_buttons.addLayout(hbox_raise)
        vbox_buttons.addWidget(fold_button)

        self.setLayout(vbox_buttons)

        self.model = game_model
        self.update_cards()
        game_model.new_card.connect(self.update_cards)

        # Controllers
        def press_fold_button():
            game_model.add_card()
        fold_button.clicked.connect(press_fold_button)

    def update_cards(self):
        print('aaa')


    def print_raise(self):
        print(self.raise_button_field.text())


class ActivePlayer(QGroupBox):
    """ Active player """
    def __init__(self):
        super().__init__("Active player")
        font = QFont()
        font.setPointSize(20)

        player_credits = QLabel(self)
        player_credits.setText('Remaining money: 250')
        player_credits.setAlignment(Qt.AlignCenter)

        player_name = QLabel(self)
        player_name.setText('Player 1')
        player_name.setMargin(20)
        player_name.setFont(font)
        player_name.setAlignment(Qt.AlignCenter)
        player_name.backgroundRole()

        hbox_cards = QHBoxLayout()
        hbox_cards.addWidget(player_card_view)

        hbox_remaining = QHBoxLayout()
        hbox_remaining.addWidget(player_credits)

        hbox = QHBoxLayout()
        hbox.addLayout(hbox_cards, 2)
        hbox.addLayout(hbox_remaining, 1)

        hbox_name = QHBoxLayout()
        hbox_name.addWidget(player_name)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_name)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.setStyleSheet("background-image: url(cards/table.png)")


class GameView(QGroupBox):
    """ main window """
    def __init__(self):
        super().__init__("main window")

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        hbox.addWidget(InputBoxLayout(model), 1)
        hbox.addWidget(ActivePlayer(), 10)

        vbox.addWidget(OtherPlayer())
        vbox.addWidget(CommunityCards())
        vbox.addLayout(hbox)

        #self.setGeometry(300, 300, 1000, 600)
        self.setWindowTitle("Texas Hold'em")
        self.setLayout(vbox)


player = model.Player()
player_card_view = CardView(player)

community_cards = model.CommunityCards()
community_card_view = CardView(community_cards)


model = model.CommunityCards()
view = GameView()
view.show()
qt_app.exec_()

'''
        card1 = QLabel(self)
        card1.setPixmap(QPixmap('cards\\2C.svg'))
        card1.setAlignment(Qt.AlignCenter)

        card2 = QLabel(self)
        card2.setPixmap(QPixmap('cards\\3C.svg'))
        card2.setAlignment(Qt.AlignCenter)

        card3 = QLabel(self)
        card3.setPixmap(QPixmap('cards\\4C.svg'))
        card3.setAlignment(Qt.AlignCenter)

        card4 = QLabel(self)
        card4.setPixmap(QPixmap('cards\\5C.svg'))
        card4.setAlignment(Qt.AlignCenter)

        card5 = QLabel(self)
        card5.setPixmap(QPixmap('cards\\6C.svg'))
        card5.setAlignment(Qt.AlignCenter)
        QPixmap()

        hbox = QHBoxLayout()
        hbox.addWidget(card1)
        hbox.addWidget(card2)
        hbox.addWidget(card3)
        hbox.addWidget(card4)
        hbox.addWidget(card5)
'''