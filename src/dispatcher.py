import os

class DispatcherGenerator:
    def __init__(self, instructions, output_dir, namespace="rv32"):
        self.instructions = sorted(instructions, key=lambda x: x.address)
        self.output_dir = output_dir
        self.namespace = namespace

    def generate(self, weights=None, block_starts=None):
        self.weights = weights if weights else {}
        self.block_starts = block_starts if block_starts else set()
        
        if self.block_starts:
            addresses = sorted(list(self.block_starts))
        else:
            addresses = [i.address for i in self.instructions]
            
        if not addresses:
            return 0

        root_path = os.path.join(self.output_dir, "root.mcfunction")
        with open(root_path, 'w') as f:
            f.write(f"scoreboard players operation #current_pc {self.namespace}_temp = pc {self.namespace}_pc\n")
            f.write(f"function {self.namespace}:dispatch/tree_root\n")

        return self._build_tree(addresses, "tree_root")

    def _get_weight(self, addr):
        return self.weights.get(addr, 1)

    def _sum_weight(self, addresses):
        return sum(self._get_weight(a) for a in addresses)

    def _build_tree(self, addresses, func_name):
        file_path = os.path.join(self.output_dir, f"{func_name}.mcfunction")
        
        with open(file_path, 'w') as f:
            if len(addresses) == 1:
                addr = addresses[0]
                prefix = "b" if self.block_starts else "i"
                f.write(f"function {self.namespace}:{prefix}_{hex(addr)[2:]}\n")
                return 1

            mid = len(addresses) // 2
            left = addresses[:mid]
            right = addresses[mid:]
            
            min_left, max_left = left[0], left[-1]
            min_right, max_right = right[0], right[-1]

            left_name = f"{func_name}_0"
            right_name = f"{func_name}_1"
            
            weight_left = self._sum_weight(left)
            weight_right = self._sum_weight(right)
            
            if weight_right > weight_left:
                f.write(f"execute if score #current_pc {self.namespace}_temp matches {min_right}..{max_right} run return run function {self.namespace}:dispatch/{right_name}\n")
                f.write(f"execute if score #current_pc {self.namespace}_temp matches {min_left}..{max_left} run return run function {self.namespace}:dispatch/{left_name}\n")
            else:
                f.write(f"execute if score #current_pc {self.namespace}_temp matches {min_left}..{max_left} run return run function {self.namespace}:dispatch/{left_name}\n")
                f.write(f"execute if score #current_pc {self.namespace}_temp matches {min_right}..{max_right} run return run function {self.namespace}:dispatch/{right_name}\n")

            left_depth = self._build_tree(left, left_name)
            right_depth = self._build_tree(right, right_name)
            return 1 + max(left_depth, right_depth)
