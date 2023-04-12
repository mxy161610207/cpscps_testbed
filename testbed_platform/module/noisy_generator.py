import random

class NoisyGenerator():
    def __init__(self) -> None:
        self._accuracy = 5 
        self._recover = [131,99,119,119]    # F B L R
        print("NoisyGenerator")

    def convert_to_sdk_distance(self,raw_dist):
        # unity顺序 F B L R
        nosiy = [0,0,0,0]
        result = [0,0,0,0]
        for i in range(4):
            if (raw_dist[i]==-1):
                result[i] = raw_dist[i]
                continue
    
            nosiy[i] = self.generate_nosiy(raw_dist[i])
            result[i] = max(0,nosiy[i]+raw_dist[i])
        
        dist_json={
            'raw': raw_dist[:],
            'noisy': nosiy[:],
            'result': result[:],
            'info': 'dist: F B L R'
        }
        return dist_json

    def generate_nosiy(self,dis):
        nosiy = random.gauss(0, self.accuracy/100 * dis)
        return int(nosiy)