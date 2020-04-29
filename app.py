from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from threading import Thread
import os
from time import time, sleep

last_submission = time()
current_delay = 0 #seconds
cipher_discovered = False
rosetta_discovered = False
phrases_discovered = False
incorrect_answers = 0
number_of_clients = 0
number_of_players = 0
answered_logic_correctly = False
client_id_map = {}

CRYPTO_SOCCER =   "a well-oiled soccer team | lost-teammate"
CRYPTO_RUSSIA =   "a russian nesting can of worms | where is todd"
CRYPTO_GEEKBOT =  "what did you do since yesterday? did you find any notable insights? | todd_is_lost"

HIVE_SCRATCH =    "A bee goes home because it has an itch"
SLACK_CHANNEL =   "A loose rope suspended between England and France"
GOOGLE_HANGOUTS = "A hundred zeros at a casual gathering"

CIPHER = "make commerce better for everyone"

CODED_MESSAGE = """
    Hello, data team :wave:. Great work in getting this far. You proved that you work well together
    and are able to solve problems together :rocket_animated:. You are quite the well-oiled soccer
    team as it were. But this next game is a real Russian nesting can-of-worms. You will have to
    prove once more that you can work together one more time. Head over to /river for the final
    challenge. Go save Todd!!! :partyblob:
"""



HEIGHT = 1080
WIDTH = 1920

ENCODING = {
    'a':'t',
    'b':'u',
    'c':'v',
    'd':'w',
    'e':'x',
    'f':'y',
    'g':'z',
    'h':'a',
    'i':'b',
    'j':'c',
    'k':'d',
    'l':'e',
    'm':'f',
    'n':'g',
    'o':'h',
    'p':'i',
    'q':'j',
    'r':'k',
    's':'l',
    't':'m',
    'u':'n',
    'v':'o',
    'w':'p',
    'x':'q',
    'y':'r',
    'z':'s'
}
DECODING = {value:key for key,value in ENCODING.items()}

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def decode_form(form):
    return dict(map(lambda x: x.split("="), form.split("&")))

def vigenere_encode(message, cipher):
    ABC = "abcdefghijklmnopqrstuvwxyz"
    cipher_length = len(cipher)
    encoded = []
    for i in range(len(message)):
        #characters not found in ABC from cipher will not change the index
        #characters not found in ABC from message will not be modified
        if ABC.find(message[i]) < 0:
            encoded.append(message[i])
        else:
            index = ABC.find(message[i]) + ABC.find(cipher[i%cipher_length]) + 1
            encoded.append(ABC[index%26])
    return "".join(encoded)

def vigenere_decode(message, cipher):
    ABC = "abcdefghijklmnopqrstuvwxyz"
    cipher_length = len(cipher)
    decoded = []
    for i in range(len(message)):
        #characters not found in ABC from cipher will not change the index
        #characters not found in ABC from message will not be modified
        if ABC.find(message[i]) < 0:
            decoded.append(message[i])
        else:
            index = ABC.find(message[i]) - ABC.find(cipher[i%cipher_length]) - 1
            decoded.append(ABC[index%26])
    return "".join(decoded)
    
class Player(object):
    
    def __init__(self, player_id):
        self.player_id = player_id
        self.x = WIDTH * 0.9
        self.y = HEIGHT * 0.5
        self.name = None
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        
class Engine(Thread):
    def __init__(self):
        super(Engine, self).__init__()
        self.players = {}
        self.running = True
    
    def tick(self):
        update = []
        for player in self.players.values():
            player.x += 10 * (player.right - player.left)
            player.y += 10 * (player.down - player.up)
            player.x = min(max(0,player.x), WIDTH)
            player.y = min(max(0,player.y), HEIGHT)
            update.append({
                "id":   player.player_id,
                "x":    player.x,
                "y":    player.y,
                "name": player.name
            })
        with app.app_context():
            socketio.emit("update", update, broadcast = True)
    def run(self):
        FPS = 60.
        t0 = time()
        while self.running:
            sleep(max(0,1/FPS - time() + t0))
            try:
                self.tick()
                t0 = time()
            except Exception as e:
                print e
                sleep(1)
            
    def reset(self):
        self.players = {}
        
    def kill(self):
        self.running = False
            
game = Engine()
game.start()

def reset_game():
    global game
    game.kill()
    game = Engine()
    
@app.route('/')
def index():
    return redirect(url_for('logic'))

@app.route('/logic')
def logic():
    return render_template('logic.html')

@app.route('/phrases')
def phrases():
    global phrases_discovered
    if not phrases_discovered:
        with app.app_context():
            socketio.emit("logging", "phrases page discovered!", broadcast = True)
        phrases_discovered = True
    # just a simple Caesar cipher
    soccer = "".join(map(lambda x: ENCODING.get(x,x),CRYPTO_SOCCER))
    russia = "".join(map(lambda x: ENCODING.get(x,x),CRYPTO_RUSSIA))
    commerce = "".join(map(lambda x: ENCODING.get(x,x),CRYPTO_GEEKBOT))
    return render_template(
        'phrases.html',
        soccer = soccer,
        russia = russia,
        commerce = commerce
    )

@app.route('/rosetta')
def rosetta():
    global cipher_discovered
    global rosetta_discovered
    if not rosetta_discovered:
        with app.app_context():
            socketio.emit("logging", "rosetta page discovered!", broadcast = True)
        rosetta_discovered = True
            
    cipher = request.args.get("cipher")
    if cipher is None:
        secret = ""
        decoder = ""
    else:
        if not cipher_discovered:
            with app.app_context():
                socketio.emit("logging", "cipher tool discovered!", broadcast = True)
            cipher_discovered = True
        secret = """
            <form id = "cipherForm">
                <label>Cipher</label>
                <input id= "cipher" type="text" name="cipher" value = "">
                <button type= "button" onclick = "decode()">Decode</button>
            </form>
        """
        decoder = """
            console.log("success")
            function decode(){
                var key = $("#cipher").val()
                var message = $("#static").text().toLowerCase()
                var ABC = "abcdefghijklmnopqrstuvwxyz"
                var decoded = ""
                var index = 0
                for (var i = 0; i < message.length; i++){
                    if (ABC.indexOf(message[i]) < 0){
                        decoded += message[i]
                    } else {
                        index = ABC.indexOf(message[i]) - ABC.indexOf(key[i%key.length]) - 1
                        decoded += ABC[(index + 26)%26]
                    }
                }
                $("#message").html("<h2>" + decoded + "</h2>")
                return false
            }
            $('#cipherForm').submit(function() {
                decode()
                return false//important so the page won't refresh
            })
        """
    return render_template(
        "rosetta.html",
        message = vigenere_encode(CODED_MESSAGE.lower(), CIPHER),
        secret = secret,
        decoder = decoder
    )


@app.route('/river')
def river():
    return render_template("river.html")

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@socketio.on('logic_solution')
def io_logic_solution(message):
    
    global last_submission
    global current_delay
    global incorrect_answers
    global answered_logic_correctly
    
    actual_solution = {
        "alice_city":    "waterloo",
        "alice_shop":    "socks",
        "bob_city":      "toronto",
        "bob_shop":      "soaps",
        "caroline_city": "ottawa",
        "caroline_shop": "candles",
        "david_city":    "montreal",
        "david_shop":    "jewellery",
    }
    if not answered_logic_correctly and time() - last_submission < current_delay:
        emit(
            "solution", 
            "<h3>Incorrect answer. Answered incorrectly {} times.".format(incorrect_answers) + 
            "<br>Must wait {} seconds before answering again</h3>".format(
                int(current_delay - time() + last_submission) + 1),
            broadcast = True
        )
        return
    submitted_solution = decode_form(message)
    name = submitted_solution.pop("name", "?????")
    last_submission = time()
    if answered_logic_correctly or submitted_solution == actual_solution:
        answered_logic_correctly = True
        emit(
            "solution", 
             """Correct!!! Move on to <a href = "/phrases">/phrases</a>""",
             broadcast = True
        )
        emit(
            "logging", 
             """Logic question answered correctly by {}""".format(name),
             broadcast = True
        )
    else:
        incorrect_answers += 1
        current_delay += 5
        emit(
            "solution", 
            "Incorrect answer. Answered incorrectly {} times.".format(incorrect_answers) + 
            "<br>Must wait {} seconds before answering again.".format(current_delay),
            broadcast = True
        )
        emit(
            "logging", 
             """Logic question answered incorrectly by {}""".format(name),
             broadcast = True
        )

@socketio.on('logic_name')
def io_logic_name(message):
    clues = {
        "yilun":     "Don't believe Khaled",
        "sunil":     "David works in Montreal",
        "vince":     "Don't Believe Mat",
        "ali":       "The person who sells socks works in Waterloo",
        "asad":      "David makes soaps",
        "calvin":    "Don't believe Michael or Sinan",
        "come":      "Bob makes soaps",
        "ella":      "Caroline works in Waterloo",
        "hanan":     "Don't believe Karen",
        "joel":      "Don't believe Yilun",
        "karen":     "Alice sells jewellery",
        "katherine": "Don't believe Ella",
        "khaled":    "Don't believe Asad",
        "mat":       "Don't believe Ali",
        "michael":   "Don't believe Karen",
        "radwan":    "Bob does not work in Ottawa",
        "ran":       "The jewellery merchant does not work in Ottawa",
        "sean":      "Caroline does not sell socks",
        "sinan":     "Don't believe Ran"
    }
    
    name = decode_form(message).get("name").lower()
    if name in clues:
        emit("clue", clues[name])
        emit("logging", "{} received their clue".format(name), broadcast = True)
    else:
        emit("clue", "Name unknown, make sure to use your first name as labelled in Slack")
    print name
    
@socketio.on('crypto_solution')
def io_crypto_solution(message):  
    response = decode_form(message)["cryptoAnswer"].lower().replace("+"," ").replace("%3f","?")
    name = decode_form(message)["name"]
    print response
    if response == CRYPTO_SOCCER.split("|")[0].strip():
        emit("response", SLACK_CHANNEL, broadcast = True)
        emit("logging", "Soccer clue decoded by {}".format(name), broadcast = True)
    elif response == CRYPTO_RUSSIA.split("|")[0].strip():
        emit("response", GOOGLE_HANGOUTS, broadcast = True)
        emit("logging", "Can-of-worms clue decoded by {}".format(name), broadcast = True)
    elif response == CRYPTO_GEEKBOT.split("|")[0].strip():
        emit("response", HIVE_SCRATCH, broadcast = True)
        emit("logging", "geekbot clue decoded by {}".format(name), broadcast = True)
    else:
        emit("response", "That is not a correct answer")
        emit("logging", "Incorrect phrase submitted by {}".format(name), broadcast = True)
        
@socketio.on('connect')
def io_connect():
    global number_of_clients
    new_player = Player(number_of_clients)
    emit("assign_id", new_player.player_id)
    number_of_clients += 1
    print "client {} connected".format(number_of_clients)
    
@socketio.on('broadcast')
def io_broadcast(message):
    emit('broadcast', message, broadcast=True)
    
@socketio.on('connect')
def io_connect():
    global number_of_clients
    number_of_clients += 1
    print "client {} connected".format(number_of_clients)
    
@socketio.on('connect_river')
def io_connect_river(name):
    global number_of_players
    new_player = Player(number_of_players)
    client_id_map[request.sid] = number_of_players
    #remove duplicate players
    to_remove = []
    for player_id in game.players:
        if game.players[player_id].name == name and name.lower() != "admin":
            to_remove.append(player_id)
    for player_id in to_remove:
        game.players.pop(player_id)
    print "connected player id {}".format(number_of_players)
    game.players[new_player.player_id] = new_player
    emit("assign_id", new_player.player_id)
    emit(
        "logging",
        "{} arrived at the river!".format(name if name.lower() != "admin" else "Todd"),
        broadcast = True
    )
    number_of_players += 1

@socketio.on('player_update')
def io_player_update(message):
    if not message["id"] in game.players:
        return
    player = game.players[message["id"]]
    player.left = message["a"]
    player.right = message["d"]
    player.up = message["w"]
    player.down = message["s"]
    player.name = message["name"]

@socketio.on('disconnect')
def io_disconnect():
    if request.sid in client_id_map:
        game.players.pop(client_id_map[request.sid], None)
    print('Client disconnected')
    

    
    
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print "app is running on port {}".format(port)
    try:
        socketio.run(app, host = '0.0.0.0', port = port)
    finally:
        game.kill()
