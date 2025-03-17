Here's the Pong game code in C:

```c
#include <SDL.h>
#include <stdlib.h>
#include <stdio.h>

#define SCREEN_WIDTH 640
#define SCREEN_HEIGHT 480

typedef struct ball_t {
    int x, y;
    int w, h;
    int dx, dy;
} ball_t;

typedef struct paddle_t {
    int x, y;
    int w, h;
    int dy;
} paddle_t;

SDL_Window *window = NULL;
SDL_Renderer *renderer = NULL;
SDL_Surface *surface = NULL;
SDL_Surface *title = NULL;
SDL_Surface *numbermap = NULL;
SDL_Surface *gameover = NULL;
SDL_Texture *texture = NULL;
SDL_Texture *t_title = NULL;
SDL_Texture *t_numbermap = NULL;
SDL_Texture *t_gameover = NULL;

int quit = 0;
int start = 0;
int winner = 0;
int score_player = 0;
int score_cpu = 0;
ball_t ball;
paddle_t paddle_player;
paddle_t paddle_cpu;

int init();
void init_game();
void check_score();
void check_collision();
void move_ball();
void move_paddle(paddle_t *p);
void move_paddle_ai();
void draw_menu();
void draw_background();
void draw_net();
void draw_ball();
void draw_paddle(paddle_t *p);
void draw_score();
void draw_game_over();

int main(int argc, char *argv[]) {
    if (init() != 0) {
        return 1;
    }

    init_game();

    while (quit == 0) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                quit = 1;
            }
            if (e.type == SDL_KEYDOWN) {
                if (e.key.keysym.sym == SDLK_ESCAPE) {
                    quit = 1;
                }
                if (e.key.keysym.sym == SDLK_SPACE && start == 0) {
                    start = 1;
                }
                if (e.key.keysym.sym == SDLK_r && start == 0) {
                    init_game();
                }
                if (e.key.keysym.sym == SDLK_UP) {
                    paddle_player.dy = -5;
                }
                if (e.key.keysym.sym == SDLK_DOWN) {
                    paddle_player.dy = 5;
                }
            }
            if (e.type == SDL_KEYUP) {
                if (e.key.keysym.sym == SDLK_UP || e.key.keysym.sym == SDLK_DOWN) {
                    paddle_player.dy = 0;
                }
            }
        }

        if (start == 1) {
            move_ball();
            move_paddle(&paddle_player);
            move_paddle_ai();
            check_collision();
            check_score();
        }

        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
        SDL_RenderClear(renderer);

        draw_background();
        if (start == 0) {
            draw_menu();
        } else {
            draw_net();
            draw_ball();
            draw_paddle(&paddle_player);
            draw_paddle(&paddle_cpu);
            draw_score();
            if (winner != 0) {
                draw_game_over();
                start = 0;
            }
        }

        SDL_RenderPresent(renderer);

        SDL_Delay(16);
    }

    SDL_FreeSurface(surface);
    SDL_FreeSurface(title);
    SDL_FreeSurface(numbermap);
    SDL_FreeSurface(gameover);
    SDL_DestroyTexture(texture);
    SDL_DestroyTexture(t_title);
    SDL_DestroyTexture(t_numbermap);
    SDL_DestroyTexture(t_gameover);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();

    return 0;
}

int init() {
    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        printf("SDL_Init Error: %s\n", SDL_GetError());
        return 1;
    }

    window = SDL_CreateWindow("Pong", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, SCREEN_WIDTH, SCREEN_HEIGHT, SDL_WINDOW_SHOWN);
    if (window == NULL) {
        printf("SDL_CreateWindow Error: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (renderer == NULL) {
        SDL_DestroyWindow(window);
        printf("SDL_CreateRenderer Error: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    surface = SDL_GetWindowSurface(window);
    title = SDL_LoadBMP("title.bmp");
    numbermap = SDL_LoadBMP("numbermap.bmp");
    gameover = SDL_LoadBMP("gameover.bmp");

    if (title == NULL || numbermap == NULL || gameover == NULL) {
        printf("SDL_LoadBMP Error: %s\n", SDL_GetError());
        SDL_DestroyRenderer(renderer);
