"""
Half-cheetah environment code with velocity target reward

Reference:
    https://github.com/katerakelly/oyster/blob/master/rlkit/envs/half_cheetah_vel.py
"""

from typing import Any, Dict, List, Tuple

import numpy as np

from meta_rl.envs import register_env
from meta_rl.envs.half_cheetah import HalfCheetahEnv


@register_env("cheetah-vel")
class HalfCheetahVelEnv(HalfCheetahEnv):
    """
    Half-cheetah environment class with velocity target reward, as described in [1].

    The code is adapted from
    https://github.com/cbfinn/maml_rl/blob/master/rllab/envs/mujoco/half_cheetah_env_rand.py

    The half-cheetah follows the dynamics from MuJoCo [2], and receives at each
    time step a reward composed of a control cost and a penalty equal to the
    difference between its current velocity and the target velocity. The tasks
    are generated by sampling the target velocities from the uniform
    distribution on [0, 2].

    [1] Chelsea Finn, Pieter Abbeel, Sergey Levine, "Model-Agnostic
        Meta-Learning for Fast Adaptation of Deep Networks", 2017
        (https://arxiv.org/abs/1703.03400)
    [2] Emanuel Todorov, Tom Erez, Yuval Tassa, "MuJoCo: A physics engine for
        model-based control", 2012
        (https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf)
    """

    def __init__(self, num_tasks: int) -> None:
        self.tasks = self.sample_tasks(num_tasks)
        self._task = self.tasks[0]
        self._goal_vel = self._task["velocity"]
        super().__init__()

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, np.float64, bool, Dict[str, Any]]:
        xposbefore = self.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.data.qpos[0]

        progress = (xposafter - xposbefore) / self.dt
        run_cost = progress - self._goal_vel
        scaled_run_cost = -1.0 * abs(run_cost)
        control_cost = 0.5 * 1e-1 * np.sum(np.square(action))

        observation = self._get_obs()
        reward = scaled_run_cost - control_cost
        done = False
        info = dict(run_cost=run_cost, control_cost=-control_cost, task=self._task)
        return observation, reward, done, info

    def sample_tasks(self, num_tasks: int):
        np.random.seed(0)
        velocities = np.random.uniform(0.0, 2.0, size=(num_tasks,))
        tasks = [{"velocity": velocity} for velocity in velocities]
        return tasks

    def get_all_task_idx(self) -> List[int]:
        return list(range(len(self.tasks)))

    def reset_task(self, idx: int) -> None:
        self._task = self.tasks[idx]
        self._goal_vel = self._task["velocity"]
        self.reset()
