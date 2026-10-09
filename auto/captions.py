"""Platform açıklamaları: format başına birkaç şablon + dönen hashtag havuzu (her gün aynı metin çıkmasın).

Kurallar (teslim/ACIKLAMALAR.md): İngilizce, 3–5 hashtag, açık "yorum yaz" dilenmesi yok (Meta düşürüyor),
YouTube başlığı ≤ 100 karakter + #shorts.
"""
import random

CORE = ["#satisfying", "#physics", "#simulation", "#oddlysatisfying"]
EXTRA = ["#asmr", "#relaxing", "#loop", "#mesmerizing", "#physicssimulation", "#visualasmr"]

T = {
    "multiply": (["Every bounce adds one more ball. Wait for the end 🤯", "One ball, then two, then… how many fit? 👀",
                  "It starts with a single ball 🔴"],
                 ["Every bounce adds a ball… until it breaks", "1 bounce = 1 new ball"], []),
    "rings": (["{n} rings. One ball. Does it make it out? 🔵", "Can it escape all {n} rings? ⭕",
               "{n} spinning rings, one tiny ball"],
              ["Can the ball escape {n} spinning rings?", "{n} rings vs 1 ball"], []),
    "pendulum": (["{n} pendulums, each a little different. Watch them line up again ⏳",
                  "Chaos… then perfect order again 〰️", "Wait for the moment they all line up"],
                 ["{n} pendulums line up again", "Pendulum wave: from chaos to order"], ["#pendulum", "#math"]),
    "laser": (["One laser bouncing inside a heart-shaped mirror ❤️", "3000 bounces later… ❤️",
               "A single laser fills a heart, one bounce at a time"],
              ["A laser trapped in a heart-shaped mirror", "1 laser, 3000 bounces, 1 heart"], ["#laser", "#art"]),
    "grow": (["It grows a little every time it bounces 🟣", "Every bounce makes it bigger. 100% is coming",
              "Watch it fill the whole circle"],
             ["Every bounce makes the ball bigger", "The ball grows every bounce"], []),
    "galton": (["{n} balls, pure chance… and still a bell curve 📈", "Random every time. Same shape every time 📈",
                "Left or right, {n} times over"],
               ["{n} random balls make a perfect bell curve", "Pure chance makes a bell curve"],
               ["#math", "#statistics"]),
    "heptagon": (["{n} balls. One small exit. Which one is last? 🌀", "Spinning walls, one tiny exit 🌀",
                  "How long until all {n} get out?"],
                 ["{n} balls, 1 tiny exit", "Can all {n} balls escape?"], []),
    "colorwar": (["{names}. The bigger your territory, the more balls you get. Who's your pick?",
                  "4 colors, 1 board, only 1 left at the end", "Pick a color before it starts"],
                 ["4 colors fight for territory. Only 1 survives", "{names}: who wins?"], ["#colorwar"]),
    "breakout": (["Every brick you break = one more ball 🧱", "One ball becomes hundreds 🧱",
                  "Watch the wall disappear"],
                 ["Every brick = +1 ball", "1 ball vs a wall of bricks"], ["#brickbreaker"]),
    "survivor": (["Pick a number before the laser does 🔴", "{n} balls, 1 laser. Which number makes it?",
                  "Only one number survives"],
                 ["{n} balls, 1 laser. Which number survives?", "Which number survives the laser?"], ["#battle"]),
    "marble_race": (["8 marbles, 1 track. Pick your color before they start 🏁", "Who takes the lead? 🏁",
                     "Pick a color. No changing it later 🏁"],
                    ["8-color marble race", "Pick a marble before the race starts"], ["#marblerace", "#race"]),
    "domino": (["The first domino is 1 cm. The last one is {size} 😳", "Each domino is a bit bigger than the last",
                "From 1 cm to {size}"],
               ["1 cm domino knocks down a {size} domino", "{n} dominoes, each bigger than the last"],
               ["#domino", "#chainreaction"]),
}


def build(fmt, params, seed):
    rng = random.Random(seed * 31 + 7)
    caps, titles, tags = T[fmt]
    v = {"n": params.get("n", ""), "size": params.get("size", ""),
         "names": ", ".join(params.get("names", [])) if params.get("names") else ""}
    cap = rng.choice(caps).format(**v)
    title = rng.choice(titles).format(**v)
    pool = tags + rng.sample(CORE, 2) + rng.sample(EXTRA, 1)
    hashtags = list(dict.fromkeys(pool))[:5]
    text = f"{cap} {' '.join(hashtags)}"
    yt_title = (title[:90] + " #shorts").strip()
    return {
        "caption": text,                                    # IG + TikTok
        "youtube_title": yt_title,
        "youtube_description": f"{cap}\n\n{' '.join(hashtags)} #shorts",
        "tags": [h.lstrip("#") for h in hashtags],
    }
