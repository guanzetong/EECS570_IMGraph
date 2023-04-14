VERTEX_NUM = 32
VAULT_NUM = 32
VERTEX_PER_VAULT = (VERTEX_NUM // VAULT_NUM) + 1

EVENT_SIZE = 4  # bytes
EVENTS_PER_ROW = 256
ROW_SIZE = EVENT_SIZE * EVENTS_PER_ROW  # 1024 bytes
ROWS_PER_BANK = 256
BANK_SIZE = ROW_SIZE * ROWS_PER_BANK  # 256 KB
BANKS_PER_VAULT = 8

def get_bank_idx(vertex_id):
    vault_idx = get_vault_idx(vertex_id)
    position_in_vault = (vertex_id - vault_idx * VERTEX_PER_VAULT) * EVENT_SIZE
    return position_in_vault // BANK_SIZE

def get_vault_idx(vertex_id):
    return vertex_id // VERTEX_PER_VAULT

def get_row_idx(vertex_id):
    bank_idx = get_bank_idx(vertex_id)
    position_in_bank = (vertex_id * EVENT_SIZE) % BANK_SIZE
    return position_in_bank // ROW_SIZE

def get_event_idx(vertex_id):
    position_in_row = (vertex_id * EVENT_SIZE) % ROW_SIZE
    return position_in_row // EVENT_SIZE


class RoundRobinArbiterVerilogStyle:
    def __init__(self, num_inputs=4):
        self.priority_counter = 0
        self.num_inputs = num_inputs

    def arbiter(self, req):
        grant = [False] * self.num_inputs

        for i in range(self.num_inputs):
            idx = (self.priority_counter + i) % self.num_inputs
            if req[idx]:
                grant[idx] = True
                break

        self.priority_counter = (self.priority_counter + 1) % self.num_inputs

        return grant

class priority_arbiter:
    def __init__(self, num_inputs=4):
        self.num_inputs = num_inputs

    def arbiter(self, req):
        grant_onehot = [False] * self.num_inputs
        grant_idx = None

        for i in range(self.num_inputs):
            idx = i
            if req[idx]:
                grant_onehot[idx] = True
                grant_idx = idx
                break


        return grant_onehot, grant_idx


# Example usage
arbiter = RoundRobinArbiterVerilogStyle()

requests = [
    [True, False, False, False],
    [True, True, False, False],
    [False, True, True, False],
    [True, False, True, False],
]

for req in requests:
    print(f"Request: {req}")
    grant = arbiter.arbiter(req)
    print(f"Grant: {grant}\n")
    