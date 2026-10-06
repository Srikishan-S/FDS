def reward(gain,latency,complexity,instability,c):
    return c.reward_performance*gain-c.reward_latency*latency-c.reward_complexity*complexity-c.reward_instability*instability
