"""
CatGPT 0.3 [CatGPT-AlphaEvolve] 20XX - AlphaEvolve Algorithm Integration
OpenRouter Edition with DeepMind's AlphaEvolve-inspired Evolution System
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import requests
import shutil
import queue
import copy
import ast
import random
import heapq
from datetime import datetime
from pathlib import Path
from threading import Thread, Lock, Event
from typing import Any, Dict, List, Tuple, Optional, Callable, Set
from html.parser import HTMLParser
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np

try:
    import aiohttp
    ASYNC_MODE = True
except ImportError:
    ASYNC_MODE = False

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Runtime Globals
RUNTIME_API_KEY: Optional[str] = None
API_KEY_LOCK = Lock()

# Runtime Paths
HOME = Path.home()
ARCHIVE_DIR = HOME / "Documents" / "CatGPT_Agent_Archive"
AGENT_WORKSPACE = ARCHIVE_DIR / "autonomous_workspace"
EVOLUTION_DIR = ARCHIVE_DIR / "evolution_history"
ALPHAEVOLVE_DIR = ARCHIVE_DIR / "alphaevolve_populations"

for path in [ARCHIVE_DIR, AGENT_WORKSPACE, EVOLUTION_DIR, ALPHAEVOLVE_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Constants
DEFAULT_MODEL = "meta-llama/llama-4-maverick:free"
LLM_TIMEOUT = 120
CODE_TIMEOUT = 60
HTTP_REFERER = "http://localhost:8000"

# AlphaEvolve Parameters
POPULATION_SIZE = 20
TOURNAMENT_SIZE = 5
MUTATION_RATE = 0.8
CROSSOVER_RATE = 0.2
ELITE_SIZE = 4
MAX_GENERATIONS = 50
DIVERSITY_THRESHOLD = 0.3
FITNESS_OBJECTIVES = ["task_success", "efficiency", "robustness", "novelty"]

# CatGPT UI Themes
UI_THEMES = {
    "dark": {
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_tertiary": "#0f1120",
        "bg_chat_display": "#0f1120",
        "bg_chat_input": "#2a2a4e",
        "bg_button_primary": "#6a0dad",
        "bg_button_success": "#28a745",
        "bg_button_danger": "#dc3545",
        "bg_button_info": "#007bff",
        "bg_evolution": "#17a2b8",
        "bg_alphaevolve": "#ff6b6b",
        "bg_listbox_select": "#9b59b6",
        "fg_primary": "#e0e0ff",
        "fg_secondary": "#b0b0cc",
        "fg_button_light": "#ffffff",
        "fg_header": "#6a0dad",
        "font_default": ("Consolas", 11),
        "font_chat": ("Consolas", 11),
        "font_button_main": ("Inter", 11, "bold"),
        "font_title": ("Inter", 14, "bold"),
        "font_listbox": ("Consolas", 10),
        "font_mission": ("Consolas", 10)
    },
    "light": {
        "bg_primary": "#f8f9fa",
        "bg_secondary": "#e9ecef",
        "bg_tertiary": "#ffffff",
        "bg_chat_display": "#ffffff",
        "bg_chat_input": "#e9ecef",
        "bg_button_primary": "#5e17eb",
        "bg_button_success": "#28a745",
        "bg_button_danger": "#dc3545",
        "bg_button_info": "#007bff",
        "bg_evolution": "#17a2b8",
        "bg_alphaevolve": "#ff6b6b",
        "bg_listbox_select": "#7c3aed",
        "fg_primary": "#212529",
        "fg_secondary": "#495057",
        "fg_button_light": "#ffffff",
        "fg_header": "#5e17eb",
        "font_default": ("Consolas", 11),
        "font_chat": ("Consolas", 11),
        "font_button_main": ("Inter", 11, "bold"),
        "font_title": ("Inter", 14, "bold"),
        "font_listbox": ("Consolas", 10),
        "font_mission": ("Consolas", 10)
    }
}

# Default theme
CURRENT_THEME = "dark"
UI_THEME = UI_THEMES[CURRENT_THEME]

# Utility Helpers
def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_api_key() -> str:
    with API_KEY_LOCK:
        if RUNTIME_API_KEY:
            return RUNTIME_API_KEY
    return ""

# HTML Parser for Web Scraping
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return ' '.join(self.text_parts).strip()

# API Client for OpenRouter
class APIClient:
    API_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key_getter: Callable[[], str], timeout: float):
        self._api_key_getter = api_key_getter
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.session_lock = asyncio.Lock()

    def _get_headers(self) -> Dict[str, str]:
        api_key = self._api_key_getter()
        if not api_key:
            raise RuntimeError("API Key is missing.")
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": HTTP_REFERER,
            "X-Title": "CatGPT Agent",
        }

    async def _get_async_session(self) -> aiohttp.ClientSession:
        async with self.session_lock:
            if self.session is None or self.session.closed:
                if ASYNC_MODE:
                    self.session = aiohttp.ClientSession()
                else:
                    raise RuntimeError("Async mode is not available. Install aiohttp.")
            return self.session

    async def call_async(self, payload: Dict[str, Any]) -> str:
        if not ASYNC_MODE:
            return self.call_sync(payload)

        session = await self._get_async_session()
        try:
            async with session.post(self.API_BASE_URL, headers=self._get_headers(), json=payload, timeout=self.timeout) as resp:
                response_json = await resp.json()
                if resp.status != 200:
                    error_text = json.dumps(response_json)
                    logger.error(f"LLM API call failed: {resp.status} - {error_text}")
                    raise RuntimeError(f"API Error ({resp.status}): {error_text}")
                return json.dumps(response_json)
        except aiohttp.ClientError as e:
            logger.error(f"Network error during async API call: {e}")
            raise RuntimeError(f"Network Error: {e}")

    def call_sync(self, payload: Dict[str, Any]) -> str:
        try:
            response = requests.post(self.API_BASE_URL, headers=self._get_headers(), json=payload, timeout=self.timeout)
            response.raise_for_status()
            return json.dumps(response.json())
        except requests.RequestException as e:
            logger.error(f"Network error during sync API call: {e}")
            raise RuntimeError(f"Network Error: {e}")

    async def close_session(self):
        async with self.session_lock:
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None

# Code Interpreter
class CodeInterpreter:
    def __init__(self, timeout: int = CODE_TIMEOUT, workspace_dir: Path = AGENT_WORKSPACE):
        self.timeout = timeout
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Code interpreter workspace: {self.workspace_dir}")

    def execute_code(self, code_string: str) -> Tuple[str, str, Optional[str], Optional[str]]:
        stdout_str, stderr_str, error_msg, saved_png_path = "", "", None, None
        with tempfile.TemporaryDirectory(dir=str(self.workspace_dir)) as temp_dir:
            temp_script_path = Path(temp_dir) / "script.py"
            try:
                temp_script_path.write_text(code_string, encoding="utf-8")
                process = subprocess.run(
                    [sys.executable, "-u", str(temp_script_path)],
                    capture_output=True, text=True, timeout=self.timeout,
                    cwd=temp_dir, check=False
                )
                stdout_str, stderr_str = process.stdout, process.stderr
                png_files = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
                if png_files:
                    png_path = Path(temp_dir) / png_files[0]
                    saved_png_path = self.workspace_dir / f"output_{now_ts()}.png"
                    shutil.copy(png_path, saved_png_path)
                    saved_png_path = str(saved_png_path)
            except subprocess.TimeoutExpired:
                error_msg = f"Code execution timed out after {self.timeout} seconds."
                stderr_str += f"\nTimeoutError: Execution exceeded {self.timeout} seconds."
            except Exception as e:
                error_msg = f"An unexpected error occurred: {e}"
                logger.error(f"Code execution error: {e}")
            finally:
                if temp_script_path.exists():
                    temp_script_path.unlink()
        return stdout_str, stderr_str, error_msg, saved_png_path

# AlphaEvolve Components
@dataclass
class AgentGenome:
    """Represents the genetic information of an agent"""
    genome_id: str
    code: str
    tools: List[str]
    system_prompt: str
    generation: int
    parents: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)
    fitness_scores: Dict[str, float] = field(default_factory=dict)
    behavioral_signature: Optional[np.ndarray] = None
    
    def calculate_diversity(self, other: 'AgentGenome') -> float:
        """Calculate behavioral diversity between two genomes"""
        if self.behavioral_signature is None or other.behavioral_signature is None:
            # Fallback to code similarity
            self_code_len = len(self.code) if self.code else 1
            other_code_len = len(other.code) if other.code else 1
            common_chars = len(set(self.code) & set(other.code)) if self.code and other.code else 0
            return 1.0 - (common_chars / max(self_code_len, other_code_len))
        return float(np.linalg.norm(self.behavioral_signature - other.behavioral_signature))

class MutationOperator(ABC):
    """Abstract base class for mutation operators"""
    @abstractmethod
    async def mutate(self, genome: AgentGenome, api_client: APIClient) -> AgentGenome:
        pass

class AddToolMutation(MutationOperator):
    """Adds a new tool to the agent"""
    
    POTENTIAL_TOOLS = [
        {
            "name": "delete_file",
            "description": "Deletes a file from the workspace",
            "code": """def delete_file(self, filename: str) -> str:
    try:
        file_path = AGENT_WORKSPACE / filename
        if file_path.exists():
            file_path.unlink()
            return f"Successfully deleted '{filename}'."
        return f"Error: File '{filename}' not found."
    except Exception as e:
        return f"Error deleting file: {e}\""""
        },
        {
            "name": "create_directory", 
            "description": "Creates a new directory",
            "code": """def create_directory(self, dirname: str) -> str:
    try:
        dir_path = AGENT_WORKSPACE / dirname
        dir_path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created directory '{dirname}'."
    except Exception as e:
        return f"Error creating directory: {e}\""""
        },
        {
            "name": "run_shell_command",
            "description": "Executes a shell command", 
            "code": """def run_shell_command(self, command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return f"STDOUT: {result.stdout}\\nSTDERR: {result.stderr}\\nReturn code: {result.returncode}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error running command: {e}\""""
        }
    ]
    
    async def mutate(self, genome: AgentGenome, api_client: APIClient) -> AgentGenome:
        # Select a random tool that's not already in genome
        available_tools = [t for t in self.POTENTIAL_TOOLS if t["name"] not in genome.tools]
        if not available_tools:
            return genome
            
        tool = random.choice(available_tools)
        new_genome = copy.deepcopy(genome)
        new_genome.genome_id = f"{genome.genome_id}_add_{tool['name']}"
        new_genome.mutations.append(f"Added tool: {tool['name']}")
        new_genome.tools.append(tool["name"])
        
        # Insert the tool code into the agent
        # First, check if EvolvingAutonomousAgent class exists
        class_pattern = r'(class EvolvingAutonomousAgent:.*?)(\n\s+def __init__)'
        match = re.search(class_pattern, new_genome.code, re.DOTALL)
        if match:
            # Find the end of __init__ method to insert after it
            init_end = new_genome.code.find('\n\n    def ', match.end())
            if init_end == -1:
                # If no method found after __init__, find the next method
                init_end = new_genome.code.find('\n    def ', match.end())
            
            if init_end != -1:
                indent = "    "
                formatted_code = "\n\n" + "\n".join(indent + line for line in tool["code"].strip().split("\n")) + "\n"
                new_genome.code = new_genome.code[:init_end] + formatted_code + new_genome.code[init_end:]
        
        return new_genome

class RefactorToolMutation(MutationOperator):
    """Uses LLM to refactor an existing tool for better performance"""
    async def mutate(self, genome: AgentGenome, api_client: APIClient) -> AgentGenome:
        if not genome.tools:
            return genome
            
        tool_to_refactor = random.choice(genome.tools)
        
        prompt = f"""Analyze and improve this tool function from an autonomous agent.
Tool name: {tool_to_refactor}

Suggest improvements for:
1. Error handling
2. Performance optimization
3. Edge case handling
4. Code clarity

Return ONLY the improved function code, nothing else."""

        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert Python developer focused on code optimization."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = await api_client.call_async(payload)
        response_data = json.loads(response)
        improved_code = response_data['choices'][0]['message']['content']
        
        new_genome = copy.deepcopy(genome)
        new_genome.genome_id = f"{genome.genome_id}_refactor_{tool_to_refactor}"
        new_genome.mutations.append(f"Refactored tool: {tool_to_refactor}")
        
        # Replace the tool implementation
        # This is simplified - in production would use AST parsing
        new_genome.code = genome.code  # Would actually replace the specific function
        
        return new_genome

class PromptEvolutionMutation(MutationOperator):
    """Evolves the system prompt for better agent behavior"""
    async def mutate(self, genome: AgentGenome, api_client: APIClient) -> AgentGenome:
        prompt = f"""Current system prompt:
{genome.system_prompt}

Create an improved version that:
1. Provides clearer guidance
2. Encourages more systematic problem-solving
3. Improves tool usage decisions
4. Maintains the core purpose

Return ONLY the new system prompt."""

        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert in prompt engineering for AI agents."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8
        }
        
        response = await api_client.call_async(payload)
        response_data = json.loads(response)
        new_prompt = response_data['choices'][0]['message']['content']
        
        new_genome = copy.deepcopy(genome)
        new_genome.genome_id = f"{genome.genome_id}_prompt_evo"
        new_genome.system_prompt = new_prompt.strip()
        new_genome.mutations.append("Evolved system prompt")
        
        return new_genome

class AlphaEvolveEngine:
    """Main evolution engine implementing AlphaEvolve algorithm"""
    def __init__(self, api_client: APIClient, ui_queue: queue.Queue):
        self.api_client = api_client
        self.ui_queue = ui_queue
        self.population: List[AgentGenome] = []
        self.generation = 0
        self.mutation_operators = [
            AddToolMutation(),
            RefactorToolMutation(),
            PromptEvolutionMutation()
        ]
        self.fitness_history = []
        self.diversity_history = []
        
    def log(self, message: str, tag: str = "alphaevolve"):
        self.ui_queue.put({"tag": tag, "content": f"[AlphaEvolve] {message}"})
        
    def initialize_population(self, base_genome: AgentGenome) -> List[AgentGenome]:
        """Create initial population with variations"""
        population = [base_genome]
        
        # Create variations of the base genome
        for i in range(POPULATION_SIZE - 1):
            variant = copy.deepcopy(base_genome)
            variant.genome_id = f"initial_variant_{i}"
            variant.generation = 0
            variant.parents = []  # Clear parents for initial variants
            variant.mutations = []  # Clear mutations for initial variants
            
            # Random mutations to create diversity
            if random.random() < 0.5:
                variant.system_prompt += f"\nVariation {i}: Focus on {random.choice(['efficiency', 'exploration', 'careful planning', 'rapid prototyping'])}."
            
            population.append(variant)
            
        self.log(f"Initialized population with {len(population)} individuals")
        return population
        
    async def evaluate_fitness(self, genome: AgentGenome, test_tasks: List[str]) -> Dict[str, float]:
        """Evaluate agent on multiple objectives"""
        fitness_scores = {
            "task_success": 0.0,
            "efficiency": 0.0,
            "robustness": 0.0,
            "novelty": 0.0
        }
        
        # Simplified evaluation - in production would actually run the agent
        # For now, assign scores based on genome properties
        
        # Task success based on tools available
        fitness_scores["task_success"] = min(1.0, len(genome.tools) * 0.15)
        
        # Efficiency based on code length (shorter is better, to a point)
        optimal_length = 5000
        code_length = len(genome.code)
        if code_length > 0:
            fitness_scores["efficiency"] = max(0.0, 1.0 - abs(code_length - optimal_length) / optimal_length)
        else:
            fitness_scores["efficiency"] = 0.0
        
        # Robustness based on error handling patterns
        error_patterns = len(re.findall(r'try:|except:', genome.code))
        fitness_scores["robustness"] = min(1.0, error_patterns * 0.1)
        
        # Novelty based on unique mutations
        fitness_scores["novelty"] = min(1.0, len(genome.mutations) * 0.2)
        
        genome.fitness_scores = fitness_scores
        
        # Calculate behavioral signature for diversity
        genome.behavioral_signature = np.array(list(fitness_scores.values()))
        
        return fitness_scores
        
    def select_parents(self, population: List[AgentGenome]) -> List[AgentGenome]:
        """Tournament selection with diversity preservation"""
        parents = []
        
        # Elite selection
        sorted_pop = sorted(population, 
                          key=lambda g: sum(g.fitness_scores.values()) if g.fitness_scores else 0, 
                          reverse=True)
        parents.extend(sorted_pop[:min(ELITE_SIZE, len(sorted_pop))])
        
        # Tournament selection for remaining slots
        while len(parents) < min(POPULATION_SIZE // 2, len(population)):
            tournament_size = min(TOURNAMENT_SIZE, len(population))
            tournament = random.sample(population, tournament_size)
            
            # Multi-objective tournament
            winner = max(tournament, key=lambda g: (
                sum(g.fitness_scores.values()) if g.fitness_scores else 0 + 
                self.calculate_diversity_bonus(g, parents)
            ))
            parents.append(winner)
            
        return parents
        
    def calculate_diversity_bonus(self, genome: AgentGenome, existing: List[AgentGenome]) -> float:
        """Calculate diversity bonus for selection"""
        if not existing:
            return 0.0
        
        try:
            min_distance = min(genome.calculate_diversity(other) for other in existing)
            return min_distance * DIVERSITY_THRESHOLD
        except (ValueError, ZeroDivisionError):
            return 0.0
        
    async def create_offspring(self, parents: List[AgentGenome]) -> List[AgentGenome]:
        """Create new generation through mutation and crossover"""
        offspring = []
        
        for parent in parents:
            # Mutation
            if random.random() < MUTATION_RATE:
                operator = random.choice(self.mutation_operators)
                try:
                    child = await operator.mutate(parent, self.api_client)
                    child.generation = self.generation + 1
                    child.parents = [parent.genome_id]
                    offspring.append(child)
                except Exception as e:
                    self.log(f"Mutation failed: {e}", "error")
                    offspring.append(copy.deepcopy(parent))
            else:
                offspring.append(copy.deepcopy(parent))
                
        # Crossover (simplified - combine system prompts)
        if len(offspring) >= 2 and random.random() < CROSSOVER_RATE:
            p1, p2 = random.sample(offspring, 2)
            child = copy.deepcopy(p1)
            child.genome_id = f"{p1.genome_id}_x_{p2.genome_id}"
            child.system_prompt = p1.system_prompt[:len(p1.system_prompt)//2] + p2.system_prompt[len(p2.system_prompt)//2:]
            child.parents = [p1.genome_id, p2.genome_id]
            child.mutations.append("Crossover")
            offspring.append(child)
            
        return offspring
        
    async def evolve_generation(self, test_tasks: List[str]) -> List[AgentGenome]:
        """Run one generation of evolution"""
        self.generation += 1
        self.log(f"Starting generation {self.generation}")
        
        # Evaluate fitness
        for genome in self.population:
            await self.evaluate_fitness(genome, test_tasks)
            
        # Log statistics
        if self.population:
            fitness_values = [sum(g.fitness_scores.values()) if g.fitness_scores else 0 for g in self.population]
            avg_fitness = np.mean(fitness_values) if fitness_values else 0
            best_fitness = max(fitness_values) if fitness_values else 0
            self.fitness_history.append((self.generation, avg_fitness, best_fitness))
            
            self.log(f"Generation {self.generation} - Avg fitness: {avg_fitness:.3f}, Best: {best_fitness:.3f}")
        else:
            self.log(f"Generation {self.generation} - No population to evaluate")
        
        # Selection
        parents = self.select_parents(self.population)
        
        # Reproduction
        offspring = await self.create_offspring(parents)
        
        # Replace population
        self.population = self.select_survivors(parents + offspring, POPULATION_SIZE)
        
        return self.population
        
    def select_survivors(self, candidates: List[AgentGenome], size: int) -> List[AgentGenome]:
        """Select survivors for next generation with diversity preservation"""
        survivors = []
        
        # Handle empty candidates
        if not candidates:
            return survivors
            
        # Sort by fitness
        sorted_candidates = sorted(candidates, 
                                 key=lambda g: sum(g.fitness_scores.values()) if g.fitness_scores else 0, 
                                 reverse=True)
        
        # Add best individuals
        elite_count = min(ELITE_SIZE, len(sorted_candidates))
        survivors.extend(sorted_candidates[:elite_count])
        
        # Add diverse individuals
        remaining = sorted_candidates[elite_count:]
        while len(survivors) < min(size, len(sorted_candidates)) and remaining:
            # Find most diverse individual
            best_diverse = max(remaining, 
                             key=lambda g: self.calculate_diversity_bonus(g, survivors))
            survivors.append(best_diverse)
            remaining.remove(best_diverse)
            
        return survivors[:size]
        
    async def run_evolution(self, base_genome: AgentGenome, generations: int, test_tasks: List[str]):
        """Run the complete evolution process"""
        self.population = self.initialize_population(base_genome)
        
        for gen in range(generations):
            await self.evolve_generation(test_tasks)
            
            # Save best genome if population exists
            if self.population:
                best_genome = max(self.population, key=lambda g: sum(g.fitness_scores.values()) if g.fitness_scores else 0)
                await self.save_genome(best_genome)
                
                if gen % 5 == 0:
                    fitness_sum = sum(best_genome.fitness_scores.values()) if best_genome.fitness_scores else 0
                    self.log(f"Checkpoint: Saved best genome with fitness {fitness_sum:.3f}")
                
        return self.population
        
    async def save_genome(self, genome: AgentGenome):
        """Save genome to disk"""
        genome_dir = ALPHAEVOLVE_DIR / f"gen_{genome.generation}" / genome.genome_id
        genome_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata = {
            "genome_id": genome.genome_id,
            "generation": genome.generation,
            "parents": genome.parents,
            "mutations": genome.mutations,
            "fitness_scores": genome.fitness_scores,
            "timestamp": now_ts()
        }
        
        with open(genome_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Save code
        with open(genome_dir / "agent_code.py", "w") as f:
            f.write(genome.code)
            
        # Save system prompt
        with open(genome_dir / "system_prompt.txt", "w") as f:
            f.write(genome.system_prompt)

# Original agent classes remain the same but with AlphaEvolve integration
class EvolvingAutonomousAgent:
    MASTER_TOOL_LIBRARY = {
        "execute_python_code": {
            "description": "Executes Python code in a sandboxed environment. Returns stdout, stderr, and system errors.",
            "args": {"code_string": "The Python code to execute."}
        },
        "write_file": {
            "description": "Writes content to a file in the agent's workspace.",
            "args": {"filename": "File name.", "content": "Content to write."}
        },
        "read_file": {
            "description": "Reads content from a file in the agent's workspace.",
            "args": {"filename": "File to read."}
        },
        "list_files": {
            "description": "Lists all files in the agent's workspace.",
            "args": {}
        },
        "search_web": {
            "description": "Fetches text content from a URL.",
            "args": {"url": "URL to retrieve."}
        },
        "task_complete": {
            "description": "Indicates the agent believes the goal is achieved, but continues running until stopped.",
            "args": {"reason": "Reason for task completion."}
        }
    }

    def __init__(self, goal: str, api_client: APIClient, code_interpreter: CodeInterpreter,
                 model_name: str, ui_queue: queue.Queue, stop_event: Event,
                 system_prompt: str, selected_tool_names: List[str], 
                 generation: int = 0, parent_id: Optional[str] = None,
                 genome: Optional[AgentGenome] = None):
        
        self.generation = generation
        self.agent_id = f"agent_gen{generation}_{now_ts()}"
        self.parent_id = parent_id
        self.performance_score = 0.0
        self.evaluation_log = []
        self.genome = genome
        
        # Store own source code for self-modification
        self.source_file = Path(__file__)
        self.source_code = self.source_file.read_text()
        
        # Regular agent initialization
        self.goal = goal
        self.api_client = api_client
        self.code_interpreter = code_interpreter
        self.model_name = model_name
        self.ui_queue = ui_queue
        self.stop_event = stop_event
        self.system_prompt = system_prompt if system_prompt else """You are CatGPT, an autonomous AI agent. Your goal is to solve problems by thinking, planning, and executing commands."""
        self.history: List[Dict[str, Any]] = []
        self.completed = False

        # Initialize tools based on current implementation
        tool_function_map = {
            "execute_python_code": self.code_interpreter.execute_code,
            "write_file": self.write_file,
            "read_file": self.read_file,
            "list_files": self.list_files,
            "search_web": self.search_web,
            "task_complete": self.task_complete
        }
        
        # Check if evolved version has new tools
        if hasattr(self, 'read_csv'):
            tool_function_map["read_csv"] = self.read_csv
        if hasattr(self, 'delete_file'):
            tool_function_map["delete_file"] = self.delete_file
        if hasattr(self, 'create_directory'):
            tool_function_map["create_directory"] = self.create_directory
        if hasattr(self, 'run_shell_command'):
            tool_function_map["run_shell_command"] = self.run_shell_command
            
        self.tools = {name: tool_function_map[name] for name in selected_tool_names if name in tool_function_map}
        
        # Update MASTER_TOOL_LIBRARY if new tools exist
        if hasattr(self, 'read_csv') and 'read_csv' not in self.MASTER_TOOL_LIBRARY:
            self.MASTER_TOOL_LIBRARY['read_csv'] = {
                "description": "Reads a CSV file and returns its contents",
                "args": {"filename": "CSV file to read."}
            }
        if hasattr(self, 'delete_file') and 'delete_file' not in self.MASTER_TOOL_LIBRARY:
            self.MASTER_TOOL_LIBRARY['delete_file'] = {
                "description": "Deletes a file from the workspace",
                "args": {"filename": "File to delete."}
            }
        if hasattr(self, 'create_directory') and 'create_directory' not in self.MASTER_TOOL_LIBRARY:
            self.MASTER_TOOL_LIBRARY['create_directory'] = {
                "description": "Creates a new directory",
                "args": {"dirname": "Directory name."}
            }
        if hasattr(self, 'run_shell_command') and 'run_shell_command' not in self.MASTER_TOOL_LIBRARY:
            self.MASTER_TOOL_LIBRARY['run_shell_command'] = {
                "description": "Executes a shell command",
                "args": {"command": "Shell command to execute."}
            }
        
        self.open_ai_tool_config = [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": self.MASTER_TOOL_LIBRARY[name]["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            arg_name: {"type": "string", "description": arg_desc}
                            for arg_name, arg_desc in self.MASTER_TOOL_LIBRARY[name]["args"].items()
                        },
                        "required": list(self.MASTER_TOOL_LIBRARY[name]["args"].keys()),
                    },
                }
            }
            for name in selected_tool_names if name in self.MASTER_TOOL_LIBRARY
        ]

    def log_to_ui(self, message: str, tag: str = "info"):
        if not self.stop_event.is_set():
            self.ui_queue.put({"tag": tag, "content": f"[Gen{self.generation}] {message}"})

    def write_file(self, filename: str, content: str) -> str:
        try:
            (AGENT_WORKSPACE / filename).write_text(content, encoding='utf-8')
            return f"Successfully wrote to '{filename}'."
        except Exception as e:
            return f"Error writing to file: {e}"

    def read_file(self, filename: str) -> str:
        try:
            return (AGENT_WORKSPACE / filename).read_text(encoding='utf-8')
        except FileNotFoundError:
            return f"Error: File '{filename}' not found."
        except Exception as e:
            return f"Error reading file: {e}"

    def list_files(self) -> str:
        try:
            files = [str(p.relative_to(AGENT_WORKSPACE)) for p in AGENT_WORKSPACE.rglob("*") if p.is_file()]
            return "Workspace files:\n" + "\n".join(files) if files else "Workspace is empty."
        except Exception as e:
            return f"Error listing files: {e}"

    def search_web(self, url: str) -> str:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            parser = TextExtractor()
            parser.feed(response.text)
            text = parser.get_text()
            return text[:4000]
        except requests.RequestException as e:
            return f"Error searching web: {e}"

    def task_complete(self, reason: str) -> str:
        self.log_to_ui(f"TASK BELIEVED COMPLETE: {reason}. Continuing to run until stopped.", "system")
        return f"Agent believes task is complete: {reason}. Awaiting user stop command."

    async def save_to_evolution_dir(self):
        """Save this agent version to the evolution directory"""
        agent_dir = EVOLUTION_DIR / self.agent_id
        agent_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata = {
            "agent_id": self.agent_id,
            "generation": self.generation,
            "parent_id": self.parent_id,
            "performance_score": self.performance_score,
            "evaluation_log": self.evaluation_log,
            "timestamp": now_ts()
        }
        
        with open(agent_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Save source code
        with open(agent_dir / "agent_code.py", "w") as f:
            f.write(self.source_code)
            
        self.log_to_ui(f"Saved agent version to {agent_dir}", "system")

    async def run(self):
        self.log_to_ui(f"EVOLVED AGENT ACTIVATED\nGOAL: {self.goal}\nMODEL: {self.model_name}\nGENERATION: {self.generation}", "system")
        
        self.history = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"My goal is: {self.goal}. Please begin."}
        ]
        
        self.log_to_ui(f"SYSTEM PROMPT INITIALIZED:\n{self.system_prompt}", "llm")

        iteration_count = 0
        while not self.stop_event.is_set():
            iteration_count += 1
            self.log_to_ui(f"--- Iteration {iteration_count} ---", "agent")

            try:
                self.log_to_ui("Thinking...", "agent")
                
                payload = {
                    "model": self.model_name,
                    "messages": self.history,
                    "tools": self.open_ai_tool_config,
                    "tool_choice": "auto"
                }
                self.log_to_ui(f"DEBUG: Sending payload to LLM: {json.dumps(payload, indent=2)}", "debug")
                
                llm_response_raw = await self.api_client.call_async(payload)
                self.log_to_ui(f"DEBUG: Raw LLM response: {llm_response_raw[:1000]}...", "debug") # Log first 1000 chars

                response_data = json.loads(llm_response_raw)
                self.log_to_ui(f"DEBUG: Parsed LLM response data: {json.dumps(response_data, indent=2)}", "debug")
                
                message = response_data['choices'][0]['message']
                self.history.append(message)

                tool_calls = message.get('tool_calls')
                
                if tool_calls:
                    self.log_to_ui(f"LLM Response (Tool Call):\n{json.dumps(tool_calls, indent=2)}", "llm")
                    
                    tool_results_for_history = []
                    for tool_call in tool_calls:
                        command_name = tool_call['function']['name']
                        try:
                            command_args = json.loads(tool_call['function']['arguments'])
                        except json.JSONDecodeError:
                            self.log_to_ui(f"ERROR: Failed to decode arguments for {command_name}: {tool_call['function']['arguments']}", "error")
                            self.evaluation_log.append(f"JSON decode error for {command_name}")
                            continue

                        self.log_to_ui(f"COMMAND: {command_name}({json.dumps(command_args)})", "agent")

                        if command_name in self.tools:
                            self.log_to_ui(f"DEBUG: Tool '{command_name}' found in self.tools.", "debug")
                            tool_func = self.tools[command_name]
                            try:
                                if command_name == 'execute_python_code':
                                    stdout, stderr, exec_err, png_path = tool_func(**command_args)
                                    tool_result = f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                                    if exec_err: 
                                        tool_result += f"\nEXECUTION_ERROR: {exec_err}"
                                        self.evaluation_log.append(f"Code execution error: {exec_err}")
                                    if png_path: tool_result += f"\nPNG generated: {png_path}"
                                else:
                                    tool_result = tool_func(**command_args)
                            except Exception as e:
                                tool_result = f"Error executing tool {command_name}: {e}"
                                self.evaluation_log.append(f"Tool execution error ({command_name}): {e}")
                                logger.error(tool_result, exc_info=True)
                        else:
                            self.log_to_ui(f"DEBUG: Tool '{command_name}' NOT found in self.tools. Available tools: {list(self.tools.keys())}", "debug")
                            tool_result = f"Error: Unknown command '{command_name}'. Available tools: {', '.join(self.tools.keys())}."
                            self.evaluation_log.append(f"Unknown command: {command_name}")
                        
                        self.log_to_ui(f"RESULT:\n{tool_result}", "result")
                        
                        tool_results_for_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "content": tool_result,
                        })
                    self.history.extend(tool_results_for_history)
                
                else:
                    text_content = message.get('content', '')
                    self.log_to_ui(f"LLM Response (Text):\n{text_content}", "llm")

                self.log_to_ui("Preparing next action...", "agent")

            except json.JSONDecodeError as e:
                error_msg = f"ERROR: JSON decode failed: {e}"
                if 'llm_response_raw' in locals():
                    error_msg += f". Raw response: {llm_response_raw[:200]}..."
                self.log_to_ui(error_msg, "error")
                self.evaluation_log.append(f"JSON decode error: {e}")
            except Exception as e:
                self.log_to_ui(f"CRITICAL ERROR: {e}", "error")
                self.evaluation_log.append(f"Critical error: {e}")
                logger.error("Critical error in agent loop", exc_info=True)
                self.stop_event.set()

        self.log_to_ui("Agent has shut down.", "system")
        await self.save_to_evolution_dir()

# Enhanced Tkinter UI with AlphaEvolve Controls
class AlphaEvolveAgentUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CatGPT 0.3 [CatGPT-AlphaEvolve] - Advanced Evolution System")
        self.geometry("1000x800")
        self.configure(bg=UI_THEME["bg_primary"])
        self.shutdown_event = Event()
        
        self.async_loop = None
        self.async_thread = None
        self.agent_task_future = None
        self.evolution_task_future = None
        self.alphaevolve_engine = None
        self.current_agent = None
        self.current_genome = None
        
        self._setup_async_loop()
        
        self._ask_for_api_key()
        if not get_api_key():
            if self.async_loop and ASYNC_MODE:
                self.async_loop.call_soon_threadsafe(self.async_loop.stop)
                if self.async_thread:
                    self.async_thread.join(timeout=2)
            self.destroy()
            sys.exit(1)
        self.api_client = APIClient(get_api_key, LLM_TIMEOUT)
        self.code_interpreter = CodeInterpreter()
        self.ui_queue = queue.Queue()
        self.alphaevolve_engine = AlphaEvolveEngine(self.api_client, self.ui_queue)
        
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Ensure proper focus for keyboard events
        self.focus_set()
        
        logger.info("CatGPT AlphaEvolve UI initialized.")

    def _setup_async_loop(self):
        if not ASYNC_MODE:
            return
        self.async_loop = asyncio.new_event_loop()
        self.async_thread = Thread(target=self.async_loop.run_forever, daemon=True)
        self.async_thread.start()
        logger.info("Asyncio event loop thread started.")

    def _ask_for_api_key(self):
        global RUNTIME_API_KEY
        temp_root = tk.Tk()
        temp_root.withdraw()

        with API_KEY_LOCK:
            key = simpledialog.askstring("API Key Required", "Enter your OpenRouter API Key:", show='*', parent=temp_root)
            if key:
                RUNTIME_API_KEY = key.strip()
                logger.info("OpenRouter API Key set.")
            else:
                logger.warning("No API key provided. Exiting.")
                messagebox.showwarning("API Key Missing", "No OpenRouter API Key provided. Exiting.", parent=temp_root)
        
        temp_root.destroy()

    def setup_ui(self):
        main_frame = ttk.Frame(self, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background=UI_THEME["bg_primary"])
        style.configure("TLabel", background=UI_THEME["bg_primary"], foreground=UI_THEME["fg_primary"], font=UI_THEME["font_default"])
        style.configure("TEntry", fieldbackground=UI_THEME["bg_chat_input"], foreground=UI_THEME["fg_primary"], insertbackground=UI_THEME["fg_primary"], font=UI_THEME["font_default"])
        
        # Goal input
        goal_frame = ttk.Frame(main_frame)
        goal_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(goal_frame, text="Goal:", font=UI_THEME["font_title"]).pack(side=tk.LEFT, padx=(0, 10))
        self.goal_entry = ttk.Entry(goal_frame, font=UI_THEME["font_default"], width=80)
        self.goal_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.goal_entry.insert(0, "Create a simple calculator in Python and save it to a file named calculator.py")

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_button = tk.Button(
            button_frame, text="Start Agent", command=self.start_agent,
            bg=UI_THEME["bg_button_primary"], fg=UI_THEME["fg_button_light"], relief=tk.FLAT,
            font=UI_THEME["font_button_main"], activebackground=UI_THEME["bg_button_success"], borderwidth=0
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5), ipady=5, ipadx=10)

        self.stop_button = tk.Button(
            button_frame, text="Stop Agent", command=self.stop_agent,
            bg=UI_THEME["bg_button_danger"], fg=UI_THEME["fg_button_light"], relief=tk.FLAT,
            font=UI_THEME["font_button_main"], state=tk.DISABLED, activebackground="#ff6b6b", borderwidth=0
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5), ipady=5, ipadx=10)

        self.alphaevolve_button = tk.Button(
            button_frame, text="Run AlphaEvolve", command=self.run_alphaevolve,
            bg=UI_THEME["bg_alphaevolve"], fg=UI_THEME["fg_button_light"], relief=tk.FLAT,
            font=UI_THEME["font_button_main"], activebackground="#dc3545", borderwidth=0
        )
        self.alphaevolve_button.pack(side=tk.LEFT, ipady=5, ipadx=10)

        # Theme toggle button
        self.theme_var = tk.StringVar(value=CURRENT_THEME)
        self.theme_button = tk.Button(
            button_frame, text="🌙 Dark" if CURRENT_THEME == "dark" else "☀️ Light", 
            command=self.toggle_theme,
            bg=UI_THEME["bg_button_info"], fg=UI_THEME["fg_button_light"], relief=tk.FLAT,
            font=UI_THEME["font_button_main"], activebackground="#0056b3", borderwidth=0
        )
        self.theme_button.pack(side=tk.RIGHT, ipady=5, ipadx=10)

        # Evolution info with AlphaEvolve stats
        evolution_frame = ttk.Frame(main_frame)
        evolution_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.generation_label = ttk.Label(evolution_frame, text="Generation: 0", font=UI_THEME["font_default"])
        self.generation_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.population_label = ttk.Label(evolution_frame, text="Population: 0", font=UI_THEME["font_default"])
        self.population_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.best_fitness_label = ttk.Label(evolution_frame, text="Best Fitness: N/A", font=UI_THEME["font_default"])
        self.best_fitness_label.pack(side=tk.LEFT)

        # AlphaEvolve parameters
        params_frame = ttk.Frame(main_frame)
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(params_frame, text="Generations:", font=UI_THEME["font_default"]).pack(side=tk.LEFT, padx=(0, 5))
        self.generations_var = tk.StringVar(value="10")
        self.generations_entry = ttk.Entry(params_frame, textvariable=self.generations_var, width=5, font=UI_THEME["font_default"])
        self.generations_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(params_frame, text="Population Size:", font=UI_THEME["font_default"]).pack(side=tk.LEFT, padx=(0, 5))
        self.population_var = tk.StringVar(value=str(POPULATION_SIZE))
        self.population_entry = ttk.Entry(params_frame, textvariable=self.population_var, width=5, font=UI_THEME["font_default"])
        self.population_entry.pack(side=tk.LEFT)

        # Output display
        self.output_text = scrolledtext.ScrolledText(
            main_frame, wrap=tk.WORD, font=UI_THEME["font_chat"],
            bg=UI_THEME["bg_chat_display"], fg=UI_THEME["fg_primary"],
            insertbackground=UI_THEME["fg_primary"], selectbackground=UI_THEME["bg_listbox_select"],
            borderwidth=0, highlightthickness=1, highlightbackground=UI_THEME["fg_header"]
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)        # Configure tags
        self.output_text.tag_configure("system", foreground="#2ecc71")
        self.output_text.tag_configure("agent", foreground="#3498db")
        self.output_text.tag_configure("tool", foreground="#f39c12")
        self.output_text.tag_configure("result", foreground="#9b59b6")
        self.output_text.tag_configure("llm", foreground="#95a5a6")
        self.output_text.tag_configure("error", foreground="#e74c3c")
        self.output_text.tag_configure("debug", foreground="#8e44ad")
        self.output_text.tag_configure("evolution", foreground="#17a2b8")
        self.output_text.tag_configure("alphaevolve", foreground="#ff6b6b")

        self.update_ui()
        
        # Apply theme after everything is set up
        self.apply_theme()

    def apply_theme(self):
        global UI_THEME
        UI_THEME = UI_THEMES[CURRENT_THEME]

        self.configure(bg=UI_THEME["bg_primary"])
        
        style = ttk.Style(self)
        style.theme_use('clam') # Or any other base theme you prefer

        style.configure("TFrame", background=UI_THEME["bg_primary"])
        style.configure("TLabel", background=UI_THEME["bg_primary"], foreground=UI_THEME["fg_primary"], font=UI_THEME["font_default"])
        style.configure("TEntry", fieldbackground=UI_THEME["bg_chat_input"], foreground=UI_THEME["fg_primary"], insertbackground=UI_THEME["fg_primary"], font=UI_THEME["font_default"])
        style.configure("TButton", background=UI_THEME["bg_button_primary"], foreground=UI_THEME["fg_button_light"], font=UI_THEME["font_button_main"], relief=tk.FLAT, borderwidth=0)
        style.map("TButton",
                  background=[('active', UI_THEME["bg_button_success"])])


        # Reconfigure specific tk widgets (not ttk)
        self.start_button.config(bg=UI_THEME["bg_button_primary"], fg=UI_THEME["fg_button_light"], activebackground=UI_THEME["bg_button_success"], font=UI_THEME["font_button_main"])
        self.stop_button.config(bg=UI_THEME["bg_button_danger"], fg=UI_THEME["fg_button_light"], activebackground="#ff6b6b", font=UI_THEME["font_button_main"]) # Assuming a lighter red for active
        self.alphaevolve_button.config(bg=UI_THEME["bg_alphaevolve"], fg=UI_THEME["fg_button_light"], activebackground="#dc3545", font=UI_THEME["font_button_main"]) # Assuming a darker red for active
        self.theme_button.config(bg=UI_THEME["bg_button_info"], fg=UI_THEME["fg_button_light"], activebackground="#0056b3", font=UI_THEME["font_button_main"]) # Assuming a darker blue for active
        self.theme_button.config(text="🌙 Dark" if CURRENT_THEME == "dark" else "☀️ Light")


        self.goal_entry.config(font=UI_THEME["font_default"])
        # For ttk.Entry, fieldbackground is set via style.configure

        self.output_text.config(
            bg=UI_THEME["bg_chat_display"], fg=UI_THEME["fg_primary"],
            insertbackground=UI_THEME["fg_primary"], selectbackground=UI_THEME["bg_listbox_select"],
            font=UI_THEME["font_chat"]
        )
        self.output_text.tag_configure("system", foreground=UI_THEMES[CURRENT_THEME].get("fg_header", "#2ecc71")) # Example: use header color for system
        self.output_text.tag_configure("agent", foreground=UI_THEMES[CURRENT_THEME].get("fg_secondary", "#3498db"))
        self.output_text.tag_configure("tool", foreground=UI_THEMES[CURRENT_THEME].get("bg_evolution", "#f39c12")) # Example: use evolution color
        self.output_text.tag_configure("result", foreground=UI_THEMES[CURRENT_THEME].get("bg_listbox_select", "#9b59b6"))
        self.output_text.tag_configure("llm", foreground=UI_THEMES[CURRENT_THEME].get("fg_secondary", "#95a5a6")) # A bit dimmer
        self.output_text.tag_configure("error", foreground=UI_THEMES[CURRENT_THEME].get("bg_button_danger", "#e74c3c"))
        self.output_text.tag_configure("evolution", foreground=UI_THEMES[CURRENT_THEME].get("bg_evolution", "#17a2b8"))
        self.output_text.tag_configure("alphaevolve", foreground=UI_THEMES[CURRENT_THEME].get("bg_alphaevolve", "#ff6b6b"))
          # Update labels
        self.generation_label.config(text=f"Generation: {self.alphaevolve_engine.generation if self.alphaevolve_engine else 0}", font=UI_THEME["font_default"])
        self.population_label.config(text=f"Population: {len(self.alphaevolve_engine.population) if self.alphaevolve_engine and self.alphaevolve_engine.population else 0}", font=UI_THEME["font_default"])
        if self.alphaevolve_engine and self.alphaevolve_engine.population:
            fitness_values = [sum(g.fitness_scores.values()) if g.fitness_scores else 0 for g in self.alphaevolve_engine.population]
            best_fitness = max(fitness_values) if fitness_values else 0
            self.best_fitness_label.config(text=f"Best Fitness: {best_fitness:.3f}", font=UI_THEME["font_default"])
        else:
            self.best_fitness_label.config(text="Best Fitness: N/A", font=UI_THEME["font_default"])

    def toggle_theme(self):
        global CURRENT_THEME, UI_THEME
        if CURRENT_THEME == "dark":
            CURRENT_THEME = "light"
        else:
            CURRENT_THEME = "dark"
        UI_THEME = UI_THEMES[CURRENT_THEME]
        self.apply_theme()
        self.log_message(f"Theme switched to {CURRENT_THEME}", "system")

    def start_agent(self):
        goal = self.goal_entry.get().strip()
        if not goal:
            messagebox.showwarning("No Goal", "Please enter a goal for the agent.")
            return

        if not get_api_key():
            messagebox.showerror("API Key Missing", "No OpenRouter API Key provided. Please restart the application.")
            return

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.shutdown_event.clear()

        # Use genome system prompt if available, otherwise use default
        if self.current_genome and hasattr(self.current_genome, 'system_prompt'):
            system_prompt = self.current_genome.system_prompt
        else:
            system_prompt = """You are CatGPT 0.3, an advanced autonomous AI agent with AlphaEvolve capabilities. 
Your goal is to solve problems by thinking, planning, and executing commands. 
You must use the provided tools to achieve the user's goal. 
Before each action, explain your reasoning and plan. 
You are part of an evolutionary system that continuously improves your capabilities."""

        selected_tools = ["execute_python_code", "write_file", "read_file", "list_files", "search_web", "task_complete"]
        
        # Add evolved tools if genome has them
        if self.current_genome and hasattr(self.current_genome, 'tools'):
            for tool in self.current_genome.tools:
                if tool not in selected_tools:
                    selected_tools.append(tool)

        # Create agent with genome if available
        generation = self.alphaevolve_engine.generation if self.alphaevolve_engine else 0
        
        agent = EvolvingAutonomousAgent(
            goal, self.api_client, self.code_interpreter,
            DEFAULT_MODEL, self.ui_queue, self.shutdown_event,
            system_prompt, selected_tools, generation, None,
            self.current_genome
        )
        
        self.current_agent = agent
        self.update_evolution_display()

        self.agent_task_future = asyncio.run_coroutine_threadsafe(agent.run(), self.async_loop)

    def stop_agent(self):
        self.shutdown_event.set()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_message("Agent stop requested by user.", "system")

    def run_alphaevolve(self):
        if not self.goal_entry.get().strip():
            messagebox.showwarning("No Goal", "Please enter a goal for evolution.")
            return
            
        self.log_message("INITIATING ALPHAEVOLVE SYSTEM...", "alphaevolve")
        self.alphaevolve_button.config(state=tk.DISABLED)
        
        # Run AlphaEvolve in async loop
        self.evolution_task_future = asyncio.run_coroutine_threadsafe(
            self._run_alphaevolve_async(), self.async_loop
        )

    async def _run_alphaevolve_async(self):
        try:
            # Create base genome
            base_genome = AgentGenome(
                genome_id="base_genome",
                code=Path(__file__).read_text(),
                tools=["execute_python_code", "write_file", "read_file", "list_files", "search_web", "task_complete"],
                system_prompt="""You are CatGPT, an autonomous AI agent. Your goal is to solve problems by thinking, planning, and executing commands.""",
                generation=0
            )
            
            # Define test tasks for fitness evaluation
            test_tasks = [
                "Create a file with content",
                "Read and modify a file",
                "Execute Python code successfully",
                "Handle errors gracefully"
            ]
            
            # Run evolution
            generations = int(self.generations_var.get())
            
            # Update POPULATION_SIZE if changed by user
            global POPULATION_SIZE
            POPULATION_SIZE = int(self.population_var.get())
            
            final_population = await self.alphaevolve_engine.run_evolution(
                base_genome, generations, test_tasks
            )
            
            # Select best genome
            if final_population:
                best_genome = max(final_population, key=lambda g: sum(g.fitness_scores.values()) if g.fitness_scores else 0)
                self.current_genome = best_genome
                
                self.ui_queue.put({
                    "tag": "alphaevolve", 
                    "content": f"AlphaEvolve complete! Best genome: {best_genome.genome_id}\n" +
                              f"Fitness scores: {json.dumps(best_genome.fitness_scores, indent=2)}"
                })
            else:
                self.ui_queue.put({
                    "tag": "error", 
                    "content": "AlphaEvolve complete but no population generated!"
                })
            
            # Update UI
            self.update_evolution_display()
            
        except Exception as e:
            self.ui_queue.put({"tag": "error", "content": f"AlphaEvolve failed: {e}"})
            logger.error("AlphaEvolve error", exc_info=True)
        finally:
            self.alphaevolve_button.config(state=tk.NORMAL)

    def update_evolution_display(self):
        if self.alphaevolve_engine:
            self.generation_label.config(text=f"Generation: {self.alphaevolve_engine.generation}")
            self.population_label.config(text=f"Population: {len(self.alphaevolve_engine.population)}")
            
            if self.alphaevolve_engine.population:
                fitness_values = [sum(g.fitness_scores.values()) if g.fitness_scores else 0 for g in self.alphaevolve_engine.population]
                best_fitness = max(fitness_values) if fitness_values else 0
                self.best_fitness_label.config(text=f"Best Fitness: {best_fitness:.3f}")
            else:
                self.best_fitness_label.config(text="Best Fitness: N/A")
        else:
            self.generation_label.config(text="Generation: 0")
            self.population_label.config(text="Population: 0")
            self.best_fitness_label.config(text="Best Fitness: N/A")

    def update_ui(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                self.log_message(msg["content"], msg.get("tag", "info"))
        except queue.Empty:
            pass
        
        if hasattr(self, 'agent_task_future') and self.agent_task_future and self.agent_task_future.done() and self.stop_button['state'] == tk.NORMAL:
            try:
                self.agent_task_future.result()
            except Exception as e:
                self.log_message(f"Agent task finished with an error: {e}", "error")
                logger.error("Agent task raised an exception", exc_info=True)
            
            self.log_message("Agent has completed its task or stopped.", "system")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.agent_task_future = None

        self.after(100, self.update_ui)

    def log_message(self, message: str, tag: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_text.insert(tk.END, f"[{timestamp}] {message}\n\n", tag)
        self.output_text.see(tk.END)

    def _on_closing(self):
        global RUNTIME_API_KEY
        logger.info("Initiating CatGPT AlphaEvolve shutdown")
        self.shutdown_event.set()
        
        if ASYNC_MODE and self.async_loop and self.async_loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self.api_client.close_session(), self.async_loop)
                future.result(timeout=5)
                logger.info("AIOHTTP session closed.")
            except Exception as e:
                logger.error(f"Error closing aiohttp session: {e}")
            finally:
                self.async_loop.call_soon_threadsafe(self.async_loop.stop)
                if self.async_thread:
                    self.async_thread.join(timeout=2)
                    logger.info("Asyncio event loop thread finished.")

        with API_KEY_LOCK:
            RUNTIME_API_KEY = None
            logger.info("API key cleared.")
        
        self.destroy()

if __name__ == "__main__":
    if not ASYNC_MODE:
        logger.warning("`aiohttp` is not installed. The agent will run in synchronous mode, which may be slower.")
    app = AlphaEvolveAgentUI()
    app.mainloop()
