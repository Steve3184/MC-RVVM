import os

class DispatcherGenerator:
    def __init__(self, instructions, output_dir, namespace="rv32"):
        self.instructions = sorted(instructions, key=lambda x: x.address)
        self.output_dir = output_dir
        self.namespace = namespace

    def generate(self):
        addresses = [i.address for i in self.instructions]
        if not addresses:
            return 0

        root_path = os.path.join(self.output_dir, "root.mcfunction")
        with open(root_path, 'w') as f:
            f.write(f"scoreboard players operation #current_pc rv_temp = pc {self.namespace}_pc\n")
            f.write(f"function {self.namespace}:dispatch/tree_root\n")

        return self._build_tree(addresses, "tree_root")

    def _build_tree(self, addresses, func_name):
        file_path = os.path.join(self.output_dir, f"{func_name}.mcfunction")
        
        with open(file_path, 'w') as f:
            if len(addresses) == 1:
                addr = addresses[0]
                f.write(f"function {self.namespace}:instr_{hex(addr)[2:]}\n")
                return 1

            mid = len(addresses) // 2
            left = addresses[:mid]
            right = addresses[mid:]
            
            min_left, max_left = left[0], left[-1]
            min_right, max_right = right[0], right[-1]

            left_name = f"{func_name}_0"
            right_name = f"{func_name}_1"

            f.write(f"execute if score #current_pc rv_temp matches {min_left}..{max_left} run function {self.namespace}:dispatch/{left_name}\n")
            f.write(f"execute if score #current_pc rv_temp matches {min_right}..{max_right} run function {self.namespace}:dispatch/{right_name}\n")

            left_depth = self._build_tree(left, left_name)
            right_depth = self._build_tree(right, right_name)
            return 1 + max(left_depth, right_depth)
