import random
import csv
import statistics

DEBUG_MODE = False

class World:
    rooms = ['A', 'B', 'C']
    states = ['CLEAN', 'DIRTY']
    room_states = [1,1,1] # hardcoded initial values. array's index refers to `rooms`, value refers to index of `states`
    
    def __init__(self, config):
        self.config = config
    
    def print_room_states(self):
        print("room states:", self.room_states)
        
    def clean_room(self, location):
        self.room_states[location] = 0
        
    def get_number_of_clean_rooms(self):
        count = 0
        for state in self.room_states:
            if state == 0:
                count += 1
        return count
        
    def next_time_step(self):
        count = 0
        for x in range(len(self.rooms)):
            # if the room is clean
            if self.room_states[x] == 0:
                result = random.random()
                if result < self.config[x]:
                    # make it dirty
                    count += 1
                    self.room_states[x] = 1
        if DEBUG_MODE and count > 0:
            print("---")
            print("🆕", count, "room(s) got dirty")
            print("---")

class Robot:
    current_room = 1
    total_movement = 0
    
    def __init__(self, world):
        self.world = world
        
    def canMoveRight(self):
        if self.current_room + 1 < len(self.world.rooms):
            return True
        return False
    
    def canMoveLeft(self):
        if self.current_room - 1 > 0:
            return True
        return False
    
    def isDirty(self):
        if self.world.room_states[self.current_room] == 1:
            return True
        return False
    
    def canPerformAction(self, action):
        if action == 'LEFT':
            return self.canMoveLeft()
        elif action == 'RIGHT':
            return self.canMoveRight()
        elif action == 'SUCK':
            return self.isDirty()
        elif action == 'NOOP':
            return True
        
    def decide(self):
        if self.isDirty():
            return 'SUCK'
        
        actions = ['LEFT', 'RIGHT', 'NOOP']
        random_action = actions[random.randint(0, 2)]
        if self.canPerformAction(random_action):
            return random_action
        
        return self.decide()
    
    def perform(self, action_to_perform):
        if action_to_perform == 'LEFT':
            self.current_room -= 1
            self.total_movement +=1
        elif action_to_perform == 'RIGHT':
            self.current_room += 1
            self.total_movement += 1
        elif action_to_perform == 'SUCK':
            self.world.clean_room(self.current_room)

class RobotV2(Robot):
    class Occurence:
        dirty=0
        total=0
        
        def dirtPossiblity(self):
            if self.total == 0:
                # we know all rooms dirty in the beginning
                return 1
            return self.dirty / self.total
        def report(self, isDirty):
            if isDirty:
                self.dirty += 1
            self.total += 1
        
    occurences = [Occurence(), Occurence(), Occurence()]
    prev_decision = 'INIT'
    # this class extends `Robot` to create a robot with better decision making
    def decide(self):
        self.occurences[self.current_room].report(self.isDirty())
        if self.isDirty():
            return 'SUCK'
        if DEBUG_MODE and (self.prev_decision == 'LEFT' or 'RIGHT'):
            print("moved into clean")
        right_posib = 0
        left_posib = 0
        if self.canMoveRight():
            right_posib = self.occurences[self.current_room + 1].dirtPossiblity()
        if self.canMoveLeft():
            left_posib = self.occurences[self.current_room - 1].dirtPossiblity()
        
        current_posib = self.occurences[self.current_room].dirtPossiblity()
        if DEBUG_MODE: 
            print("room #", self.current_room, "::","left_posib", left_posib,"::","current_posib:", current_posib,"::", "right_posib", right_posib)
            
        decision = 'RIGHT' if right_posib > left_posib else 'LEFT'
        if DEBUG_MODE:
            print('made decision:', decision)
            
        self.prev_decision = decision
        return decision

def setup(config):
    w = World(config)
    r = RobotV2(w)
    
    if DEBUG_MODE:
        print('# SETUP #')
        w.print_room_states()
        print('canMoveRight', r.canMoveRight())
        print('canMoveLeft', r.canMoveLeft())
        print('isDirty', r.isDirty())
        print('---')
    return [w,r]
    
def loop(w, r):
    total_reward = 0
    RUN_STEP = 1000
    for i in range(RUN_STEP):
        action_to_perform = r.decide()
        r.perform(action_to_perform)
        reward_this_turn = w.get_number_of_clean_rooms()
        total_reward += reward_this_turn
        w.next_time_step()
        
        if DEBUG_MODE:
            print("timestamp:", i)
            print("\tperformed:", action_to_perform)
            print("\treward_this_turn:", reward_this_turn)
            print("\ttotal_reward:", total_reward)
            print("\ttotal_movement:", r.total_movement)
            
    if DEBUG_MODE:
        print("\n🟢:",total_reward - r.total_movement,"🏆Reward:", total_reward, "❌Penalty:", r.total_movement)
    return [total_reward, r.total_movement]
    
def run_simulation(configs):
    results = {}
    for i, config in enumerate(configs):
        agent_1_rewards = []
        agent_2_rewards = []
        for j in range(10):
            [w,r] = setup(config)
            [total_reward, total_movement] = loop(w,r)
            agent_1_rewards.append(total_reward)
            agent_2_rewards.append(total_reward - total_movement)
        results[i] = {
            'agent_1_mean': statistics.mean(agent_1_rewards),
            'agent_1_std_dev': statistics.stdev(agent_1_rewards),
            'agent_2_mean': statistics.mean(agent_2_rewards),
            'agent_2_std_dev': statistics.stdev(agent_2_rewards)
        }
    agent_1_all_configs_mean = statistics.mean([results[i]['agent_1_mean'] for i in range(len(configs))])
    agent_2_all_configs_mean = statistics.mean([results[i]['agent_2_mean'] for i in range(len(configs))])
    return results, agent_1_all_configs_mean, agent_2_all_configs_mean

def export_csv(configs, results, agent_1_mean, agent_2_mean, output_file):
    with open(output_file, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Configuration', 'Agent 1 mean', 'Agent 1 std dev', 'Agent 2 mean', 'Agent 2 std dev'])
        for i, config in enumerate(configs):
            writer.writerow([f'Configuration {i+1}', results[i]['agent_1_mean'], results[i]['agent_1_std_dev'], results[i]['agent_2_mean'], results[i]['agent_2_std_dev']])
        writer.writerow(['Overall mean', agent_1_mean, '', agent_2_mean, ''])
        
def main():
    configs = [
        [.3,.3,.3], [.5,.2,.1], [.2,.4,.2], [.5,.1,.3], [.5,.3,.8]
    ]
    
    # for i, config in enumerate(configs):
    #     [w,r] = setup(config)
    #     [total_reward, total_movement] = loop(w,r)
            
    results, agent_1_mean, agent_2_mean = run_simulation(configs)
    export_csv(configs, results, agent_1_mean, agent_2_mean, 'report.csv')
    
if __name__ == "__main__":
    main()