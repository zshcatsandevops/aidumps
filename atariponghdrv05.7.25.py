<!DOCTYPE html>
<html>
<head>
    <title>Atari Pong by DeepSeek AI</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #000;
            flex-direction: column;
        }
        #gameContainer {
            position: relative;
            width: 800px;
            height: 400px;
            background: #000;
            border: 2px solid #fff;
        }
        .paddle {
            position: absolute;
            width: 15px;
            height: 80px;
            background: #fff;
        }
        #ball {
            position: absolute;
            width: 10px;
            height: 10px;
            background: #fff;
            border-radius: 50%;
        }
        .score {
            position: absolute;
            color: #fff;
            font-size: 2em;
            font-family: 'Courier New', monospace;
            top: 20px;
        }
        #player1Score {
            left: 30%;
        }
        #player2Score {
            right: 30%;
        }
        .center-line {
            position: absolute;
            width: 2px;
            height: 20px;
            background: #fff;
            left: 50%;
        }
        .volume-slider {
            margin-top: 20px;
            accent-color: #fff;
        }
    </style>
</head>
<body>
    <div id="gameContainer">
        <div id="player1" class="paddle"></div>
        <div id="player2" class="paddle"></div>
        <div id="ball"></div>
        <div id="player1Score" class="score">0</div>
        <div id="player2Score" class="score">0</div>
        <!-- Center line -->
        <div class="center-line" style="top: 0px;"></div>
        <div class="center-line" style="top: 40px;"></div>
        <div class="center-line" style="top: 80px;"></div>
        <div class="center-line" style="top: 120px;"></div>
        <div class="center-line" style="top: 160px;"></div>
        <div class="center-line" style="top: 200px;"></div>
        <div class="center-line" style="top: 240px;"></div>
        <div class="center-line" style="top: 280px;"></div>
        <div class="center-line" style="top: 320px;"></div>
        <div class="center-line" style="top: 360px;"></div>
    </div>

    <!-- Volume Control -->
    <input type="range" class="volume-slider" min="0" max="1" value="0.5" step="0.01">

    <script>
        const gameContainer = document.getElementById('gameContainer');
        const player1 = document.getElementById('player1');
        const player2 = document.getElementById('player2');
        const ball = document.getElementById('ball');
        const player1Score = document.getElementById('player1Score');
        const player2Score = document.getElementById('player2Score');
        const volumeSlider = document.querySelector('.volume-slider');

        let player1Y = 160;
        let player2Y = 160;
        let ballX = 395;
        let ballY = 195;
        let ballSpeedX = 4;
        let ballSpeedY = 4;
        let score1 = 0;
        let score2 = 0;
        let gameOver = false;

        let audioContext = new (window.AudioContext || window.webkitAudioContext)();
        let globalGain = audioContext.createGain();
        globalGain.connect(audioContext.destination);
        globalGain.gain.value = volumeSlider.value;

        volumeSlider.addEventListener('input', (e) => {
            globalGain.gain.setValueAtTime(e.target.value, audioContext.currentTime);
        });

        function playBeep(frequency = 440, duration = 0.1) {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            oscillator.type = 'square';
            oscillator.connect(gainNode);
            gainNode.connect(globalGain);
            oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + duration);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
        }

        player1.style.left = '20px';
        player2.style.right = '20px';

        gameContainer.addEventListener('mousemove', function(e) {
            if (gameOver) return;
            const rect = gameContainer.getBoundingClientRect();
            let mouseY = e.clientY - rect.top;
            player1Y = Math.max(0, Math.min(320, mouseY - 40));
        });

        function resetBall() {
            ballX = 395;
            ballY = 195;
            ballSpeedX = Math.random() > 0.5 ? 4 : -4;
            ballSpeedY = Math.random() > 0.5 ? 4 : -4;
        }

        function showGameOver(winnerText) {
            const gameOverDiv = document.createElement('div');
            gameOverDiv.id = 'gameOver';
            gameOverDiv.style.position = 'absolute';
            gameOverDiv.style.width = '100%';
            gameOverDiv.style.height = '100%';
            gameOverDiv.style.background = 'rgba(0,0,0,0.8)';
            gameOverDiv.style.display = 'flex';
            gameOverDiv.style.flexDirection = 'column';
            gameOverDiv.style.alignItems = 'center';
            gameOverDiv.style.justifyContent = 'center';
            gameOverDiv.style.color = 'white';
            gameOverDiv.innerHTML = `
                <h1>GAME OVER</h1>
                <h2>${winnerText}</h2>
                <button id="restartButton" style="margin-top: 20px; padding: 10px 20px; font-size: 1.2em;">
                    Play Again
                </button>
            `;
            
            gameContainer.appendChild(gameOverDiv);
            document.getElementById('restartButton').addEventListener('click', () => {
                gameOver = false;
                score1 = 0;
                score2 = 0;
                player1Score.textContent = '0';
                player2Score.textContent = '0';
                gameContainer.removeChild(gameOverDiv);
                resetBall();
                updateGame();
            });
        }

        function updateGame() {
            if (gameOver) return;
            player1.style.top = player1Y + 'px';

            let aiCenter = player2Y + 40;
            if (aiCenter < ballY) player2Y = Math.min(320, player2Y + 4);
            else if (aiCenter > ballY) player2Y = Math.max(0, player2Y - 4);
            player2.style.top = player2Y + 'px';

            ballX += ballSpeedX;
            ballY += ballSpeedY;
            ball.style.left = ballX + 'px';
            ball.style.top = ballY + 'px';

            if (ballY <= 0 || ballY >= 390) {
                ballSpeedY = -ballSpeedY;
                playBeep(150, 0.05);
            }

            if ((ballX <= 35 && ballY >= player1Y && ballY <= player1Y + 80) ||
                (ballX >= 750 && ballY >= player2Y && ballY <= player2Y + 80)) {
                ballSpeedX = -ballSpeedX;
                playBeep(250, 0.1);
            }

            if (ballX <= 0 && !gameOver) {
                score2++;
                player2Score.textContent = score2;
                
                if (score2 === 5) {
                    gameOver = true;
                    showGameOver('Player 2 Wins!');
                    return;
                }
                resetBall();
                playBeep(350, 0.2);
                playBeep(175, 0.2);
            }

            if (ballX >= 790 && !gameOver) {
                score1++;
                player1Score.textContent = score1;
                
                if (score1 === 5) {
                    gameOver = true;
                    showGameOver('Player 1 Wins!');
                    return;
                }
                resetBall();
                playBeep(350, 0.2);
                playBeep(175, 0.2);
            }

            requestAnimationFrame(updateGame);
        }

        updateGame();
    </script>
</body>
</html>


