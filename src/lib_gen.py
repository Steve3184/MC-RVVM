import os

class LibGenerator:
    def __init__(self, output_dir, namespace="rv32"):
        self.output_dir = output_dir
        self.namespace = namespace
        self.lib_costs = {}

    def generate(self):
        for d in ["lib", "mem", "ecall", "debug"]:
            os.makedirs(os.path.join(self.output_dir, d), exist_ok=True)
        self.gen_bitwise()
        self.gen_shifts()
        self.gen_math()
        self.gen_mem()
        self.gen_load_batch()
        ascii_depth = self.gen_uart()
        self.gen_data_loader()
        self.gen_exec_cmd()
        self.gen_read_nbt()
        self.gen_write_nbt()
        self.gen_gpu()
        self.gen_sleep()
        self.gen_ecall()
        self.gen_debug()
        return ascii_depth, self.lib_costs

    def _register_cost(self, name, lines, deps=None):
        count = len(lines) if isinstance(lines, list) else lines
        dep_cost = 0
        if deps:
            for d in deps:
                if isinstance(d, tuple):
                    d_name, multiplier = d
                    dep_cost += self.lib_costs.get(d_name, 0) * multiplier
                else:
                    dep_cost += self.lib_costs.get(d, 0)
        self.lib_costs[name] = count + dep_cost
    
    def gen_gpu(self):
        palette_lines = [
            f'data modify storage {self.namespace}:gpu palette set value []',
            f'data remove storage {self.namespace}:temp gpu_batch'
        ]
        batch_size = 128
        batch = []
        for i in range(4096):
            r = ((i >> 8) & 0xF) * 17
            g = ((i >> 4) & 0xF) * 17
            b = (i & 0xF) * 17
            hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
            batch.append(f'{{"text":".","color":"{hex_color}"}}')
            if len(batch) >= batch_size:
                batch_str = ",".join(batch)
                palette_lines.append(f'data modify storage {self.namespace}:temp gpu_batch set value [{batch_str}]')
                palette_lines.append(f'data modify storage {self.namespace}:gpu palette append from storage {self.namespace}:temp gpu_batch[]')
                batch = []
        if batch:
            batch_str = ",".join(batch)
            palette_lines.append(f'data modify storage {self.namespace}:temp gpu_batch set value [{batch_str}]')
            palette_lines.append(f'data modify storage {self.namespace}:gpu palette append from storage {self.namespace}:temp gpu_batch[]')
        
        palette_lines.append(f'data remove storage {self.namespace}:temp gpu_batch')
        palette_lines.append(f'data modify storage {self.namespace}:gpu palette append value {{"text":"\\\\n"}}')
        
        with open(os.path.join(self.output_dir, "lib", "init_gpu.mcfunction"), 'w') as f:
            f.write("\n".join(palette_lines) + "\n")

        with open(os.path.join(self.output_dir, "ecall", "screen_init.mcfunction"), 'w') as f:
            f.write("kill @e[type=text_display,tag=%s_screen]\n" % self.namespace)
            f.write(f"scoreboard players set #scale {self.namespace}_temp 1000\n")
            f.write(f"scoreboard players set #c_100 {self.namespace}_temp 100\n")
            f.write(f"scoreboard players set #c_10 {self.namespace}_temp 10\n")
            f.write(f"scoreboard players set #minus_one {self.namespace}_temp -1\n")
            
            for g in range(10):
                for l in range(4):
                    ox, oy = (0, 0)
                    if l == 1: ox = 25
                    if l == 2: oy = -25
                    if l == 3: ox, oy = 25, -25
                    
                    group_base_idx = g // 2
                    group_offset = group_base_idx * -50
                    total_oy = oy + group_offset
                    f.write(f"data modify storage {self.namespace}:io layer set value {l}\n")
                    f.write(f"data modify storage {self.namespace}:io group set value {g}\n")
                    f.write(f"scoreboard players set #ox {self.namespace}_temp {ox}\n")
                    f.write(f"scoreboard players set #oy {self.namespace}_temp {total_oy}\n")
                    
                    f.write(f"function {self.namespace}:ecall/screen_calc_pos\n")
                    f.write(f"function {self.namespace}:ecall/screen_summon_entity with storage {self.namespace}:io\n")
            
            f.write(f"function {self.namespace}:lib/init_gpu\n")
        
        with open(os.path.join(self.output_dir, "ecall", "screen_calc_pos.mcfunction"), 'w') as f:
            f.write(f"scoreboard players set #scale {self.namespace}_temp 1000\n")
            f.write(f"scoreboard players set #c_100 {self.namespace}_temp 100\n")
            f.write(f"scoreboard players set #c_10 {self.namespace}_temp 10\n")
            f.write(f"scoreboard players set #minus_one {self.namespace}_temp -1\n")

            def write_axis_calc(axis_prefix, reg_name, offset_var=None):
                f.write(f'data modify storage {self.namespace}:io {axis_prefix}s set value ""\n')
                f.write(f"execute store result score #val {self.namespace}_temp run scoreboard players get {reg_name} {self.namespace}_reg\n")
                f.write(f"scoreboard players operation #val {self.namespace}_temp *= #scale {self.namespace}_temp\n")
                if offset_var:
                    f.write(f"scoreboard players operation #val {self.namespace}_temp += {offset_var} {self.namespace}_temp\n")
                
                f.write(f'execute if score #val {self.namespace}_temp matches ..-1 run data modify storage {self.namespace}:io {axis_prefix}s set value "-"\n')
                f.write(f"execute if score #val {self.namespace}_temp matches ..-1 run scoreboard players operation #val {self.namespace}_temp *= #minus_one {self.namespace}_temp\n")
                
                f.write(f"scoreboard players operation #int_part {self.namespace}_temp = #val {self.namespace}_temp\n")
                f.write(f"scoreboard players operation #int_part {self.namespace}_temp /= #scale {self.namespace}_temp\n")
                f.write(f"execute store result storage {self.namespace}:io {axis_prefix}i int 1 run scoreboard players get #int_part {self.namespace}_temp\n")

                f.write(f"scoreboard players operation #dec_part {self.namespace}_temp = #val {self.namespace}_temp\n")
                f.write(f"scoreboard players operation #dec_part {self.namespace}_temp %= #scale {self.namespace}_temp\n")
                
                f.write(f"scoreboard players operation #d1 {self.namespace}_temp = #dec_part {self.namespace}_temp\n")
                f.write(f"scoreboard players operation #d1 {self.namespace}_temp /= #c_100 {self.namespace}_temp\n")
                f.write(f"execute store result storage {self.namespace}:io {axis_prefix}d1 int 1 run scoreboard players get #d1 {self.namespace}_temp\n")
                
                f.write(f"scoreboard players operation #d2 {self.namespace}_temp = #dec_part {self.namespace}_temp\n")
                f.write(f"scoreboard players operation #d2 {self.namespace}_temp %= #c_100 {self.namespace}_temp\n")
                f.write(f"scoreboard players operation #d2 {self.namespace}_temp /= #c_10 {self.namespace}_temp\n")
                f.write(f"execute store result storage {self.namespace}:io {axis_prefix}d2 int 1 run scoreboard players get #d2 {self.namespace}_temp\n")
                
                f.write(f"scoreboard players operation #d3 {self.namespace}_temp = #dec_part {self.namespace}_temp\n")
                f.write(f"scoreboard players operation #d3 {self.namespace}_temp %= #c_10 {self.namespace}_temp\n")
                f.write(f"execute store result storage {self.namespace}:io {axis_prefix}d3 int 1 run scoreboard players get #d3 {self.namespace}_temp\n")

            write_axis_calc("x", "x10", "#ox")
            write_axis_calc("y", "x11", "#oy")
            write_axis_calc("z", "x12", None)

        with open(os.path.join(self.output_dir, "ecall", "screen_summon_entity.mcfunction"), 'w') as f:
            lines_summon = [
                "$summon text_display $(xs)$(xi).$(xd1)$(xd2)$(xd3) $(ys)$(yi).$(yd1)$(yd2)$(yd3) $(zs)$(zi).$(zd1)$(zd2)$(zd3) {Tags:[\"$(self)_screen\",\"$(self)_screen_$(group)\",\"$(self)_screen_$(group)_$(layer)\"],billboard:\"fixed\",alignment:\"left\",background:0,text:'\"\"'}"
            ]
            content = "\n".join(lines_summon).replace("$(self)", self.namespace)
            f.write(content + "\n")

        with open(os.path.join(self.output_dir, "ecall", "screen_flush_apply.mcfunction"), 'w') as f:
            for g in range(10):
                for l in range(4):
                    f.write(f"data modify entity @e[type=text_display,tag={self.namespace}_screen_{g}_{l},limit=1] text set value '\"\"'\n")
                    f.write(f"$execute if data storage {self.namespace}:gpu buf_{g}_{l}[0] run data modify entity @e[type=text_display,tag={self.namespace}_screen_{g}_{l},limit=1] text set value '$(buf_{g}_{l})'\n")

        with open(os.path.join(self.output_dir, "ecall", "screen_flush.mcfunction"), 'w') as f:
            for g in range(10):
                for l in range(4):
                    f.write(f"data modify storage {self.namespace}:gpu buf_{g}_{l} set value []\n")
            f.write(f"scoreboard players operation #addr {self.namespace}_temp = x10 {self.namespace}_reg\n")
            f.write(f"scoreboard players set #curr_y {self.namespace}_temp 0\n")
            f.write(f"function {self.namespace}:ecall/screen_flush_row\n")
            f.write(f"function {self.namespace}:ecall/screen_flush_apply with storage {self.namespace}:gpu\n")

        with open(os.path.join(self.output_dir, "ecall", "screen_flush_row.mcfunction"), 'w') as f:
            f.write(f"execute if score #curr_y {self.namespace}_temp matches 40.. run return 0\n")
            f.write(f"scoreboard players set #curr_x {self.namespace}_temp 0\n")
            f.write(f"scoreboard players operation #group {self.namespace}_temp = #curr_y {self.namespace}_temp\n")
            f.write(f"scoreboard players set #ten {self.namespace}_const 10\n")
            f.write(f"scoreboard players operation #group {self.namespace}_temp %= #ten {self.namespace}_const\n")
            f.write(f"function {self.namespace}:ecall/screen_flush_pixel\n")
            f.write(f"scoreboard players add #curr_y {self.namespace}_temp 1\n")
            f.write(f"function {self.namespace}:ecall/screen_flush_row\n")

        with open(os.path.join(self.output_dir, "ecall", "screen_flush_pixel.mcfunction"), 'w') as f:
            f.write(f"execute if score #curr_x {self.namespace}_temp matches 48.. run return 0\n")
            f.write(f"scoreboard players operation #addr_word {self.namespace}_temp = #addr {self.namespace}_temp\n")
            f.write(f"scoreboard players operation #addr_word {self.namespace}_temp /= #four {self.namespace}_const\n")
            f.write(f"execute store result storage {self.namespace}:io addr int 1 run scoreboard players get #addr_word {self.namespace}_temp\n")
            f.write(f"scoreboard players operation #off {self.namespace}_temp = #addr {self.namespace}_temp\n")
            f.write(f"scoreboard players operation #off {self.namespace}_temp %= #four {self.namespace}_const\n")
            f.write(f"execute store result storage {self.namespace}:io off int 1 run scoreboard players get #off {self.namespace}_temp\n")
            f.write(f"function {self.namespace}:mem/read_lhu with storage {self.namespace}:io\n")
            f.write(f"scoreboard players operation #lx {self.namespace}_temp = #curr_x {self.namespace}_temp\n")
            f.write(f"scoreboard players operation #lx {self.namespace}_temp %= #two {self.namespace}_const\n")
            f.write(f"scoreboard players operation #ly {self.namespace}_temp = #curr_y {self.namespace}_temp\n")
            f.write(f"scoreboard players operation #ly {self.namespace}_temp %= #two {self.namespace}_const\n")
            f.write(f"scoreboard players operation #layer {self.namespace}_temp = #ly {self.namespace}_temp\n")
            f.write(f"scoreboard players operation #layer {self.namespace}_temp *= #two {self.namespace}_const\n")
            f.write(f"scoreboard players operation #layer {self.namespace}_temp += #lx {self.namespace}_temp\n")
            f.write(f"execute store result storage {self.namespace}:gpu col_idx int 1 run scoreboard players get #res {self.namespace}_temp\n")
            f.write(f"execute store result storage {self.namespace}:gpu g int 1 run scoreboard players get #group {self.namespace}_temp\n")
            f.write(f"execute store result storage {self.namespace}:gpu l int 1 run scoreboard players get #layer {self.namespace}_temp\n")
            f.write(f"function {self.namespace}:ecall/screen_append_pixel with storage {self.namespace}:gpu\n")
            nl_cmd = f"function {self.namespace}:ecall/screen_append_nl with storage {self.namespace}:gpu"
            f.write(f"execute if score #lx {self.namespace}_temp matches 0 if score #curr_x {self.namespace}_temp matches 46 run {nl_cmd}\n")
            f.write(f"execute if score #lx {self.namespace}_temp matches 1 if score #curr_x {self.namespace}_temp matches 47 run {nl_cmd}\n")
            f.write(f"scoreboard players add #addr {self.namespace}_temp 2\n")
            f.write(f"scoreboard players add #curr_x {self.namespace}_temp 1\n")
            f.write(f"function {self.namespace}:ecall/screen_flush_pixel\n")

        with open(os.path.join(self.output_dir, "ecall", "screen_append_pixel.mcfunction"), 'w') as f:
            f.write(f"$data modify storage {self.namespace}:gpu buf_$(g)_$(l) append from storage {self.namespace}:gpu palette[$(col_idx)]\n")
        
        with open(os.path.join(self.output_dir, "ecall", "screen_append_nl.mcfunction"), 'w') as f:
            f.write(f"$data modify storage {self.namespace}:gpu buf_$(g)_$(l) append from storage {self.namespace}:gpu palette[4096]\n")

    def gen_sleep(self):
        with open(os.path.join(self.output_dir, "ecall", "sleep.mcfunction"), 'w') as f:
            f.write(f"scoreboard players operation #sleep_ticks {self.namespace}_temp = x10 {self.namespace}_reg\n")
            f.write(f"scoreboard players set #ipt_count {self.namespace}_temp 0\n")

        with open(os.path.join(self.output_dir, "lib", "sleep_tick.mcfunction"), 'w') as f:
            f.write(f"execute if score #sleep_ticks {self.namespace}_temp matches 1.. run scoreboard players remove #sleep_ticks {self.namespace}_temp 1\n")

    def gen_exec_cmd(self):
        MAX_CMD_LEN = 4096
        lines_init = [f'data modify storage {self.namespace}:cmd_template args set value {{}}']
        batch = []
        for i in range(MAX_CMD_LEN):
            batch.append(f'"{i}":""')
            if len(batch) >= 100:
                lines_init.append(f'data modify storage {self.namespace}:cmd_template args merge value {{{",".join(batch)}}}')
                batch = []
        if batch:
            lines_init.append(f'data modify storage {self.namespace}:cmd_template args merge value {{{",".join(batch)}}}')

        with open(os.path.join(self.output_dir, "lib", "init_cmd_template.mcfunction"), "w") as f:
            f.write("\n".join(lines_init) + "\n")

        with open(os.path.join(self.output_dir, "ecall", "exec_cmd_resolve_char.mcfunction"), "w") as f:
            f.write(f"$data modify storage {self.namespace}:io_cmd char set from storage {self.namespace}:ascii table[$(char_idx)]\n")
            f.write(f"function {self.namespace}:ecall/exec_cmd_append_char with storage {self.namespace}:io_cmd\n")

        with open(os.path.join(self.output_dir, "ecall", "exec_cmd_append_char.mcfunction"), "w") as f:
            f.write(f"$data modify storage {self.namespace}:io_cmd args.$(idx) set value '$(char)'\n")

        lengths = [256, 512, 1024, 2048, 3072, 4096]
        for l in lengths:
            self._gen_exec_cmd_variant(l)

    def _gen_exec_cmd_variant(self, length):
        lines = [
            f"data modify storage {self.namespace}:io_cmd args set from storage {self.namespace}:cmd_template args",
            f"scoreboard players set #idx {self.namespace}_temp 0",
            f"scoreboard players operation #addr {self.namespace}_temp = x10 {self.namespace}_reg",
            f"function {self.namespace}:ecall/exec_cmd_loop_{length}",
            f"function {self.namespace}:ecall/exec_cmd_run_macro_{length} with storage {self.namespace}:io_cmd args"
        ]
        with open(os.path.join(self.output_dir, "ecall", f"exec_cmd_{length}.mcfunction"), "w") as f:
            f.write("\n".join(lines) + "\n")
            
        lines_loop = [
            f"execute if score #idx {self.namespace}_temp matches {length}.. run return 0",
            f"scoreboard players operation #off {self.namespace}_temp = #addr {self.namespace}_temp",
            f"scoreboard players operation #off {self.namespace}_temp %= #four {self.namespace}_const",
            f"execute if score #off {self.namespace}_temp matches ..-1 run scoreboard players add #off {self.namespace}_temp 4",
            f"scoreboard players operation #addr_word {self.namespace}_temp = #addr {self.namespace}_temp",
            f"scoreboard players operation #addr_word {self.namespace}_temp /= #four {self.namespace}_const",
            f"execute store result storage {self.namespace}:io_cmd addr int 1 run scoreboard players get #addr_word {self.namespace}_temp",
            f"function {self.namespace}:mem/read_lw with storage {self.namespace}:io_cmd",
            f"scoreboard players operation #w {self.namespace}_temp = #res {self.namespace}_temp",
            f"scoreboard players set #valid {self.namespace}_temp 4",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #valid {self.namespace}_temp -= #off {self.namespace}_temp",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #op1 {self.namespace}_temp = #w {self.namespace}_temp",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #op2 {self.namespace}_temp = #off {self.namespace}_temp",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #op2 {self.namespace}_temp *= #p_3 {self.namespace}_const",
            f"execute if score #off {self.namespace}_temp matches 1.. run function {self.namespace}:lib/srl",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #w {self.namespace}_temp = #res {self.namespace}_temp",
            f"execute if score #valid {self.namespace}_temp matches ..0 run function {self.namespace}:ecall/exec_cmd_next_word_{length}",
            f"execute if score #valid {self.namespace}_temp matches ..0 run return 0",
            f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp",
            f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches 0 run return 0",
            
            f"execute store result storage {self.namespace}:io_cmd char_idx int 1 run scoreboard players get #byte {self.namespace}_temp",
            f"execute store result storage {self.namespace}:io_cmd idx int 1 run scoreboard players get #idx {self.namespace}_temp",
            f"function {self.namespace}:ecall/exec_cmd_resolve_char with storage {self.namespace}:io_cmd",
            
            f"scoreboard players add #idx {self.namespace}_temp 1",
            f"scoreboard players remove #valid {self.namespace}_temp 1",
            f"execute if score #valid {self.namespace}_temp matches ..0 run function {self.namespace}:ecall/exec_cmd_next_word_{length}",
            f"execute if score #valid {self.namespace}_temp matches ..0 run return 0",
            f"execute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp -= #min_int {self.namespace}_const",
            f"scoreboard players operation #w {self.namespace}_temp /= #p_8 {self.namespace}_const",
            f"execute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp += #p_23 {self.namespace}_const",
            f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp",
            f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches 0 run return 0",
            f"execute store result storage {self.namespace}:io_cmd char_idx int 1 run scoreboard players get #byte {self.namespace}_temp",
            f"execute store result storage {self.namespace}:io_cmd idx int 1 run scoreboard players get #idx {self.namespace}_temp",
            f"function {self.namespace}:ecall/exec_cmd_resolve_char with storage {self.namespace}:io_cmd",
            f"scoreboard players add #idx {self.namespace}_temp 1",
            f"scoreboard players remove #valid {self.namespace}_temp 1",
            f"execute if score #valid {self.namespace}_temp matches ..0 run function {self.namespace}:ecall/exec_cmd_next_word_{length}",
            f"execute if score #valid {self.namespace}_temp matches ..0 run return 0",
            f"scoreboard players operation #w {self.namespace}_temp /= #p_8 {self.namespace}_const",
            f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp",
            f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches 0 run return 0",
            f"execute store result storage {self.namespace}:io_cmd char_idx int 1 run scoreboard players get #byte {self.namespace}_temp",
            f"execute store result storage {self.namespace}:io_cmd idx int 1 run scoreboard players get #idx {self.namespace}_temp",
            f"function {self.namespace}:ecall/exec_cmd_resolve_char with storage {self.namespace}:io_cmd",
            f"scoreboard players add #idx {self.namespace}_temp 1",
            f"scoreboard players remove #valid {self.namespace}_temp 1",
            f"execute if score #valid {self.namespace}_temp matches ..0 run function {self.namespace}:ecall/exec_cmd_next_word_{length}",
            f"execute if score #valid {self.namespace}_temp matches ..0 run return 0",
            f"scoreboard players operation #w {self.namespace}_temp /= #p_8 {self.namespace}_const",
            f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp",
            f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches 0 run return 0",
            f"execute store result storage {self.namespace}:io_cmd char_idx int 1 run scoreboard players get #byte {self.namespace}_temp",
            f"execute store result storage {self.namespace}:io_cmd idx int 1 run scoreboard players get #idx {self.namespace}_temp",
            f"function {self.namespace}:ecall/exec_cmd_resolve_char with storage {self.namespace}:io_cmd",
            f"scoreboard players add #idx {self.namespace}_temp 1",

            f"function {self.namespace}:ecall/exec_cmd_next_word_{length}"
        ]
        with open(os.path.join(self.output_dir, "ecall", f"exec_cmd_loop_{length}.mcfunction"), "w") as f:
            f.write("\n".join(lines_loop) + "\n")

        with open(os.path.join(self.output_dir, "ecall", f"exec_cmd_next_word_{length}.mcfunction"), "w") as f:
            lines_next = [
                f"scoreboard players operation #off {self.namespace}_temp = #addr {self.namespace}_temp",
                f"scoreboard players operation #off {self.namespace}_temp %= #four {self.namespace}_const",
                f"execute if score #off {self.namespace}_temp matches ..-1 run scoreboard players add #off {self.namespace}_temp 4",
                f"scoreboard players operation #next {self.namespace}_temp = #four {self.namespace}_const",
                f"scoreboard players operation #next {self.namespace}_temp -= #off {self.namespace}_temp",
                f"scoreboard players operation #addr {self.namespace}_temp += #next {self.namespace}_temp",
                f"function {self.namespace}:ecall/exec_cmd_loop_{length}",
            ]
            f.write("\n".join(lines_next) + "\n")

        macro_str = "$" + "".join([f"$({i})" for i in range(length)])
        with open(os.path.join(self.output_dir, "ecall", f"exec_cmd_run_macro_{length}.mcfunction"), "w") as f:
             f.write(macro_str + "\n")


    def gen_data_loader(self):
        lines_main = [
            f"$data modify storage {self.namespace}:temp CopyList set from storage $(path) $(nbt)",
            f"execute store result score #curr_idx {self.namespace}_temp run data get storage {self.namespace}:io dest_idx",
            f"function {self.namespace}:mem/copy_loop"
        ]
        with open(os.path.join(self.output_dir, "mem", "copy_storage_to_ram.mcfunction"), 'w') as f:
            f.write("\n".join(lines_main) + "\n")
        self._register_cost("mem/copy_storage_to_ram", lines_main)
        with open(os.path.join(self.output_dir, "load_extra_data.mcfunction"), 'w') as f:
            f.write("# dummy file\n")
        
        lines_loop = [
            f"execute unless data storage {self.namespace}:temp CopyList[0] run return 0",
            f"execute store result storage {self.namespace}:io idx int 1 run scoreboard players get #curr_idx {self.namespace}_temp",
            f"function {self.namespace}:mem/copy_step with storage {self.namespace}:io",
            f"data remove storage {self.namespace}:temp CopyList[0]",
            f"scoreboard players add #curr_idx {self.namespace}_temp 1",
            f"function {self.namespace}:mem/copy_loop"
        ]
        with open(os.path.join(self.output_dir, "mem", "copy_loop.mcfunction"), 'w') as f:
             f.write("\n".join(lines_loop) + "\n")
        
        lines_step = [
            f"$data modify storage {self.namespace}:ram data[$(idx)] set from storage {self.namespace}:temp CopyList[0]"
        ]
        with open(os.path.join(self.output_dir, "mem", "copy_step.mcfunction"), 'w') as f:
             f.write("\n".join(lines_step) + "\n")

    def gen_load_batch(self):
        lines = [
            f"execute store result storage {self.namespace}:io idx int 1 run scoreboard players get #temp {self.namespace}_temp",
            f"function {self.namespace}:mem/load_batch_step with storage {self.namespace}:io",
            f"data remove storage {self.namespace}:temp Batch[0]",
            f"scoreboard players add #temp {self.namespace}_temp 1",
            f"execute if data storage {self.namespace}:temp Batch[0] run function {self.namespace}:mem/load_batch"
        ]
        with open(os.path.join(self.output_dir, "mem", "load_batch.mcfunction"), 'w') as f:
            f.write("\n".join(lines) + "\n")

        lines_step = [
            f"$data modify storage {self.namespace}:ram data[$(idx)] set from storage {self.namespace}:temp Batch[0]"
        ]
        with open(os.path.join(self.output_dir, "mem", "load_batch_step.mcfunction"), 'w') as f:
            f.write("\n".join(lines_step) + "\n")

    def gen_ascii_map(self):
        lines_table = [f'data modify storage {self.namespace}:ascii table set value []']
        for _ in range(32):
            lines_table.append(f'data modify storage {self.namespace}:ascii table append value ""')
        
        for i in range(32, 127):
            if i == 92:
                s_content = "\\\\\\\\"
            elif i == 39:
                s_content = "\\\\'"
            elif i == 34:
                s_content = '\\"'
            else:
                s_content = chr(i).replace('"', '\\"')
                
            lines_table.append(f'data modify storage {self.namespace}:ascii table append value "{s_content}"')
        
        for _ in range(127, 256):
             lines_table.append(f'data modify storage {self.namespace}:ascii table append value ""')
             
        os.makedirs(os.path.join(self.output_dir, "lib", "ascii"), exist_ok=True)
        with open(os.path.join(self.output_dir, "lib", "ascii", "init_table.mcfunction"), 'w') as f:
            f.write("\n".join(lines_table) + "\n")

        def generate_tree(chars, path):
            os.makedirs(os.path.join(self.output_dir, "lib", "ascii", os.path.dirname(path)), exist_ok=True)
            with open(os.path.join(self.output_dir, "lib", "ascii", f"{path}.mcfunction"), 'w') as f:
                if len(chars) == 1:
                    c, val = chars[0]
                    escaped = c.replace('\\', '\\\\').replace('"', '\\"')
                    f.write(f'data modify storage {self.namespace}:uart char set value "{escaped}"\n')
                    macro_escaped = c.replace('\\', '\\\\\\\\').replace('"', '\\\\\\"')
                    f.write(f'data modify storage {self.namespace}:uart char_esc set value "{macro_escaped}"\n')
                    self._register_cost(f"lib/ascii/{path}", 2)
                    return 1
                chunk_size = (len(chars) + 3) // 4
                chunks = [chars[i:i + chunk_size] for i in range(0, len(chars), chunk_size)]
                max_depth = 0
                for i, chunk in enumerate(chunks):
                    if not chunk: continue
                    f.write(f"execute if score #char {self.namespace}_temp matches {chunk[0][1]}..{chunk[-1][1]} run function {self.namespace}:lib/ascii/{path}_{i}\n")
                    depth = generate_tree(chunk, f"{path}_{i}")
                    max_depth = max(max_depth, depth)
                self._register_cost(f"lib/ascii/{path}", len(chunks)) 
                return 1 + max_depth
        
        all_chars = [(chr(i), i) for i in range(32, 127)]
        all_chars.sort(key=lambda x: x[1])
        return generate_tree(all_chars, "map")
    def gen_uart(self):
        ascii_depth = self.gen_ascii_map()
        
        lines_flush = [
            f"execute if data storage {self.namespace}:uart buffer[0] run tellraw @a {{\"nbt\":\"buffer[]\",\"storage\":\"{self.namespace}:uart\",\"separator\":\"\"}}",
            f"data modify storage {self.namespace}:uart buffer set value []"
        ]
        with open(os.path.join(self.output_dir, "lib", "uart_flush.mcfunction"), 'w') as f:
            f.write("\n".join(lines_flush) + "\n")
        self._register_cost("lib/uart_flush", lines_flush)
        
        lines_putc = [
            f"scoreboard players operation #char {self.namespace}_temp = x10 {self.namespace}_reg",
            f"execute if score #char {self.namespace}_temp matches 10 run function {self.namespace}:lib/uart_flush",
            f"execute unless score #char {self.namespace}_temp matches 10 run execute store result storage {self.namespace}:io char_idx int 1 run scoreboard players get #char {self.namespace}_temp",
            f"execute unless score #char {self.namespace}_temp matches 10 run function {self.namespace}:lib/uart_append_macro with storage {self.namespace}:io"
        ]
        with open(os.path.join(self.output_dir, "lib", "uart_putc.mcfunction"), 'w') as f:
            f.write("\n".join(lines_putc) + "\n")
        
        with open(os.path.join(self.output_dir, "lib", "uart_append_macro.mcfunction"), 'w') as f:
            f.write(f'$data modify storage {self.namespace}:uart buffer append from storage {self.namespace}:ascii table[$(char_idx)]\n')

        self._register_cost("lib/uart_putc", lines_putc, deps=["lib/uart_flush"])
        self.lib_costs["lib/uart_putc"] = len(lines_putc) + 2
        
        return ascii_depth

    def gen_math(self):
        mul_lines = []
        mul_lines.append(f"scoreboard players set #res {self.namespace}_temp 0")
        mul_lines.append(f"scoreboard players operation #t1 {self.namespace}_temp = #op1 {self.namespace}_temp")
        mul_lines.append(f"scoreboard players operation #t2 {self.namespace}_temp = #op2 {self.namespace}_temp")
        for i in range(32):
            mul_lines.append(f"scoreboard players operation #bit {self.namespace}_temp = #t2 {self.namespace}_temp")
            mul_lines.append(f"scoreboard players operation #bit {self.namespace}_temp %= #two {self.namespace}_const")
            mul_lines.append(f"execute unless score #bit {self.namespace}_temp matches 0 run scoreboard players operation #res {self.namespace}_temp += #t1 {self.namespace}_temp")
            mul_lines.append(f"scoreboard players operation #t1 {self.namespace}_temp *= #two {self.namespace}_const")
            mul_lines.append(f"scoreboard players operation #t2 {self.namespace}_temp /= #two {self.namespace}_const")
        
        with open(os.path.join(self.output_dir, "lib", "mul.mcfunction"), 'w') as f:
            f.write("\n".join(mul_lines) + "\n")
        self._register_cost("lib/mul", mul_lines)
        
        lines_add64 = [
            f"scoreboard players operation #rh {self.namespace}_temp += #u1h {self.namespace}_temp",
            f"scoreboard players operation #old_rl {self.namespace}_temp = #rl {self.namespace}_temp",
            f"scoreboard players operation #rl {self.namespace}_temp += #u1l {self.namespace}_temp",
            f"scoreboard players operation #c1 {self.namespace}_temp = #rl {self.namespace}_temp",
            f"scoreboard players operation #c1 {self.namespace}_temp -= #min_int {self.namespace}_const",
            f"scoreboard players operation #c2 {self.namespace}_temp = #old_rl {self.namespace}_temp",
            f"scoreboard players operation #c2 {self.namespace}_temp -= #min_int {self.namespace}_const",
            f"execute if score #c1 {self.namespace}_temp < #c2 {self.namespace}_temp run scoreboard players add #rh {self.namespace}_temp 1"
        ]
        with open(os.path.join(self.output_dir, "lib", "add64_u1.mcfunction"), 'w') as f:
            f.write("\n".join(lines_add64) + "\n")
        self._register_cost("lib/add64_u1", lines_add64)

        lines_shl64 = [
            f"scoreboard players operation #u1h {self.namespace}_temp *= #two {self.namespace}_const",
            f"execute if score #u1l {self.namespace}_temp matches ..-1 run scoreboard players add #u1h {self.namespace}_temp 1",
            f"scoreboard players operation #u1l {self.namespace}_temp *= #two {self.namespace}_const"
        ]
        with open(os.path.join(self.output_dir, "lib", "shl64_u1.mcfunction"), 'w') as f:
            f.write("\n".join(lines_shl64) + "\n")
        self._register_cost("lib/shl64_u1", lines_shl64)

        for op in ["mulh", "mulhu", "mulhsu"]:
            lines = []
            lines.append(f"scoreboard players set #rh {self.namespace}_temp 0\nscoreboard players set #rl {self.namespace}_temp 0")
            lines.append(f"scoreboard players operation #u1l {self.namespace}_temp = #op1 {self.namespace}_temp\nscoreboard players set #u1h {self.namespace}_temp 0")
            lines.append(f"scoreboard players operation #u2l {self.namespace}_temp = #op2 {self.namespace}_temp\nscoreboard players set #u2h {self.namespace}_temp 0")
            if op == "mulh":
                lines.append(f"execute if score #op1 {self.namespace}_temp matches ..-1 run scoreboard players set #u1h {self.namespace}_temp -1")
                lines.append(f"execute if score #op2 {self.namespace}_temp matches ..-1 run scoreboard players set #u2h {self.namespace}_temp -1")
            elif op == "mulhsu":
                lines.append(f"execute if score #op1 {self.namespace}_temp matches ..-1 run scoreboard players set #u1h {self.namespace}_temp -1")
            for i in range(32):
                lines.append(f"scoreboard players operation #bit {self.namespace}_temp = #u2l {self.namespace}_temp")
                lines.append(f"scoreboard players operation #bit {self.namespace}_temp %= #two {self.namespace}_const")
                lines.append(f"execute unless score #bit {self.namespace}_temp matches 0 run function {self.namespace}:lib/add64_u1")
                lines.append(f"function {self.namespace}:lib/shl64_u1")
                lines.append(f"scoreboard players operation #op1 {self.namespace}_temp = #u2l {self.namespace}_temp")
                lines.append(f"scoreboard players set #op2 {self.namespace}_temp 1")
                lines.append(f"function {self.namespace}:lib/srl")
                lines.append(f"scoreboard players operation #u2l {self.namespace}_temp = #res {self.namespace}_temp")
            lines.append(f"scoreboard players operation #res {self.namespace}_temp = #rh {self.namespace}_temp")
            
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f:
                f.write("\n".join(lines) + "\n")
            self._register_cost(f"lib/{op}", lines, deps=[("lib/add64_u1", 32), ("lib/shl64_u1", 32), ("lib/srl", 32)])

        divu_lines = []
        divu_lines.append(f"scoreboard players set #q {self.namespace}_temp 0\nscoreboard players set #r {self.namespace}_temp 0")
        divu_lines.append(f"execute if score #u2 {self.namespace}_temp matches 0 run scoreboard players set #q {self.namespace}_temp -1")
        divu_lines.append(f"execute if score #u2 {self.namespace}_temp matches 0 run scoreboard players operation #r {self.namespace}_temp = #u1 {self.namespace}_temp")
        divu_lines.append(f"execute if score #u2 {self.namespace}_temp matches 0 run return 0")
        divu_lines.append(f"scoreboard players operation #tu2 {self.namespace}_temp = #u2 {self.namespace}_temp")
        divu_lines.append(f"scoreboard players operation #tu2 {self.namespace}_temp -= #min_int {self.namespace}_const")
        for i in range(31, -1, -1):
            divu_lines.append(f"scoreboard players operation #r {self.namespace}_temp *= #two {self.namespace}_const")
            if i == 31:
                divu_lines.append(f"scoreboard players set #bit {self.namespace}_temp 0")
                divu_lines.append(f"execute if score #u1 {self.namespace}_temp matches ..-1 run scoreboard players set #bit {self.namespace}_temp 1")
            else:
                divu_lines.append(f"scoreboard players operation #bit {self.namespace}_temp = #u1 {self.namespace}_temp")
                if i > 0: divu_lines.append(f"scoreboard players operation #bit {self.namespace}_temp /= #p_{i} {self.namespace}_const")
                divu_lines.append(f"scoreboard players operation #bit {self.namespace}_temp %= #two {self.namespace}_const")
                divu_lines.append(f"execute if score #bit {self.namespace}_temp matches ..-1 run scoreboard players add #bit {self.namespace}_temp 2")
            divu_lines.append(f"scoreboard players operation #r {self.namespace}_temp += #bit {self.namespace}_temp")
            divu_lines.append(f"scoreboard players operation #tr {self.namespace}_temp = #r {self.namespace}_temp")
            divu_lines.append(f"scoreboard players operation #tr {self.namespace}_temp -= #min_int {self.namespace}_const")
            divu_lines.append(f"execute if score #tr {self.namespace}_temp >= #tu2 {self.namespace}_temp run scoreboard players operation #r {self.namespace}_temp -= #u2 {self.namespace}_temp")
            if i > 0: divu_lines.append(f"execute if score #tr {self.namespace}_temp >= #tu2 {self.namespace}_temp run scoreboard players operation #q {self.namespace}_temp += #p_{i} {self.namespace}_const")
            else: divu_lines.append(f"execute if score #tr {self.namespace}_temp >= #tu2 {self.namespace}_temp run scoreboard players add #q {self.namespace}_temp 1")
        
        with open(os.path.join(self.output_dir, "lib", "divu_logic.mcfunction"), 'w') as f:
            f.write("\n".join(divu_lines) + "\n")
        self._register_cost("lib/divu_logic", divu_lines)

        for op in ["divu", "remu", "div", "rem"]:
            lines = []
            if op == "divu":
                lines.append(f"scoreboard players operation #u1 {self.namespace}_temp = #op1 {self.namespace}_temp")
                lines.append(f"scoreboard players operation #u2 {self.namespace}_temp = #op2 {self.namespace}_temp")
                lines.append(f"function {self.namespace}:lib/divu_logic")
                lines.append(f"scoreboard players operation #res {self.namespace}_temp = #q {self.namespace}_temp")
            elif op == "remu":
                lines.append(f"scoreboard players operation #u1 {self.namespace}_temp = #op1 {self.namespace}_temp")
                lines.append(f"scoreboard players operation #u2 {self.namespace}_temp = #op2 {self.namespace}_temp")
                lines.append(f"function {self.namespace}:lib/divu_logic")
                lines.append(f"scoreboard players operation #res {self.namespace}_temp = #r {self.namespace}_temp")
            elif op in ["div", "rem"]:
                lines.append(f"scoreboard players set #s1 {self.namespace}_temp 0\nscoreboard players set #s2 {self.namespace}_temp 0")
                lines.append(f"execute if score #op1 {self.namespace}_temp matches ..-1 run scoreboard players set #s1 {self.namespace}_temp 1")
                lines.append(f"execute if score #op2 {self.namespace}_temp matches ..-1 run scoreboard players set #s2 {self.namespace}_temp 1")
                lines.append(f"scoreboard players operation #u1 {self.namespace}_temp = #op1 {self.namespace}_temp")
                lines.append(f"execute if score #s1 {self.namespace}_temp matches 1 run scoreboard players set #zero {self.namespace}_temp 0")
                lines.append(f"execute if score #s1 {self.namespace}_temp matches 1 run scoreboard players operation #u1 {self.namespace}_temp = #zero {self.namespace}_temp")
                lines.append(f"execute if score #s1 {self.namespace}_temp matches 1 run scoreboard players operation #u1 {self.namespace}_temp -= #op1 {self.namespace}_temp")
                lines.append(f"scoreboard players operation #u2 {self.namespace}_temp = #op2 {self.namespace}_temp")
                lines.append(f"execute if score #s2 {self.namespace}_temp matches 1 run scoreboard players set #zero {self.namespace}_temp 0")
                lines.append(f"execute if score #s2 {self.namespace}_temp matches 1 run scoreboard players operation #u2 {self.namespace}_temp = #zero {self.namespace}_temp")
                lines.append(f"execute if score #s2 {self.namespace}_temp matches 1 run scoreboard players operation #u2 {self.namespace}_temp -= #op2 {self.namespace}_temp")
                lines.append(f"function {self.namespace}:lib/divu_logic")
                if op == "div":
                    lines.append(f"scoreboard players operation #res {self.namespace}_temp = #q {self.namespace}_temp")
                    lines.append(f"execute unless score #s1 {self.namespace}_temp = #s2 {self.namespace}_temp if score #q {self.namespace}_temp matches 1.. run scoreboard players set #zero {self.namespace}_temp 0")
                    lines.append(f"execute unless score #s1 {self.namespace}_temp = #s2 {self.namespace}_temp if score #q {self.namespace}_temp matches 1.. run scoreboard players operation #res {self.namespace}_temp = #zero {self.namespace}_temp")
                    lines.append(f"execute unless score #s1 {self.namespace}_temp = #s2 {self.namespace}_temp if score #q {self.namespace}_temp matches 1.. run scoreboard players operation #res {self.namespace}_temp -= #q {self.namespace}_temp")
                else:
                    lines.append(f"scoreboard players operation #res {self.namespace}_temp = #r {self.namespace}_temp")
                    lines.append(f"execute if score #s1 {self.namespace}_temp matches 1 if score #r {self.namespace}_temp matches 1.. run scoreboard players set #zero {self.namespace}_temp 0")
                    lines.append(f"execute if score #s1 {self.namespace}_temp matches 1 if score #r {self.namespace}_temp matches 1.. run scoreboard players operation #res {self.namespace}_temp = #zero {self.namespace}_temp")
                    lines.append(f"execute if score #s1 {self.namespace}_temp matches 1 if score #r {self.namespace}_temp matches 1.. run scoreboard players operation #res {self.namespace}_temp -= #r {self.namespace}_temp")
            
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f:
                f.write("\n".join(lines) + "\n")
            self._register_cost(f"lib/{op}", lines, deps=["lib/divu_logic"])

    def gen_bitwise(self):
        for op in ["and", "or", "xor"]:
            lines = [
                f"scoreboard players set #res {self.namespace}_temp 0",
                f"scoreboard players operation #t1 {self.namespace}_temp = #op1 {self.namespace}_temp",
                f"scoreboard players operation #t2 {self.namespace}_temp = #op2 {self.namespace}_temp",
                f"execute if score #t1 {self.namespace}_temp matches ..-1 run scoreboard players operation #t1 {self.namespace}_temp -= #min_int {self.namespace}_const",
                f"execute if score #t2 {self.namespace}_temp matches ..-1 run scoreboard players operation #t2 {self.namespace}_temp -= #min_int {self.namespace}_const"
            ]
            for i in range(31):
                lines.append(f"scoreboard players operation #b1 {self.namespace}_temp = #t1 {self.namespace}_temp")
                lines.append(f"scoreboard players operation #b1 {self.namespace}_temp %= #two {self.namespace}_const")
                lines.append(f"execute if score #b1 {self.namespace}_temp matches ..-1 run scoreboard players add #b1 {self.namespace}_temp 2")
                lines.append(f"scoreboard players operation #b2 {self.namespace}_temp = #t2 {self.namespace}_temp")
                lines.append(f"scoreboard players operation #b2 {self.namespace}_temp %= #two {self.namespace}_const")
                lines.append(f"execute if score #b2 {self.namespace}_temp matches ..-1 run scoreboard players add #b2 {self.namespace}_temp 2")
                if op == "and":
                    lines.append(f"execute if score #b1 {self.namespace}_temp matches 1 if score #b2 {self.namespace}_temp matches 1 run scoreboard players operation #res {self.namespace}_temp += #p_{i} {self.namespace}_const")
                elif op == "or":
                    lines.append(f"execute if score #b1 {self.namespace}_temp matches 1 run scoreboard players operation #res {self.namespace}_temp += #p_{i} {self.namespace}_const")
                    lines.append(f"execute unless score #b1 {self.namespace}_temp matches 1 if score #b2 {self.namespace}_temp matches 1 run scoreboard players operation #res {self.namespace}_temp += #p_{i} {self.namespace}_const")
                elif op == "xor":
                    lines.append(f"execute unless score #b1 {self.namespace}_temp = #b2 {self.namespace}_temp run scoreboard players operation #res {self.namespace}_temp += #p_{i} {self.namespace}_const")
                lines.append(f"scoreboard players operation #t1 {self.namespace}_temp /= #two {self.namespace}_const")
                lines.append(f"scoreboard players operation #t2 {self.namespace}_temp /= #two {self.namespace}_const")
            lines.extend([
                f"scoreboard players set #s1 {self.namespace}_temp 0",
                f"scoreboard players set #s2 {self.namespace}_temp 0",
                f"execute if score #op1 {self.namespace}_temp matches ..-1 run scoreboard players set #s1 {self.namespace}_temp 1",
                f"execute if score #op2 {self.namespace}_temp matches ..-1 run scoreboard players set #s2 {self.namespace}_temp 1"
            ])
            if op == "and":
                lines.append(f"execute if score #s1 {self.namespace}_temp matches 1 if score #s2 {self.namespace}_temp matches 1 run scoreboard players operation #res {self.namespace}_temp -= #min_int {self.namespace}_const")
            elif op == "or":
                lines.append(f"execute if score #s1 {self.namespace}_temp matches 1 run scoreboard players operation #res {self.namespace}_temp -= #min_int {self.namespace}_const")
                lines.append(f"execute unless score #s1 {self.namespace}_temp matches 1 if score #s2 {self.namespace}_temp matches 1 run scoreboard players operation #res {self.namespace}_temp -= #min_int {self.namespace}_const")
            elif op == "xor":
                lines.append(f"execute unless score #s1 {self.namespace}_temp = #s2 {self.namespace}_temp run scoreboard players operation #res {self.namespace}_temp -= #min_int {self.namespace}_const")
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f:
                f.write("\n".join(lines))

    def gen_shifts(self):
        for op in ["sll", "srl", "sra"]:
            lines = [
                f"scoreboard players operation #res {self.namespace}_temp = #op1 {self.namespace}_temp",
                f"scoreboard players operation #amt {self.namespace}_temp = #op2 {self.namespace}_temp",
                f"scoreboard players operation #amt {self.namespace}_temp %= #thirty_two {self.namespace}_const"
            ]
            for i in range(5):
                amt = 1 << i
                lines.append(f"scoreboard players operation #bit {self.namespace}_temp = #amt {self.namespace}_temp")
                lines.append(f"scoreboard players operation #bit {self.namespace}_temp %= #two {self.namespace}_const")
                if op == "sll":
                    lines.append(f"execute if score #bit {self.namespace}_temp matches 1 run scoreboard players operation #res {self.namespace}_temp *= #p_{amt} {self.namespace}_const")
                elif op == "srl":
                    lines.append(f"execute if score #bit {self.namespace}_temp matches 1 if score #res {self.namespace}_temp matches 0.. run scoreboard players operation #res {self.namespace}_temp /= #p_{amt} {self.namespace}_const")
                    lines.append(f"execute if score #bit {self.namespace}_temp matches 1 if score #res {self.namespace}_temp matches ..-1 run function {self.namespace}:lib/srl_{amt}_neg")
                elif op == "sra":
                    lines.append(f"execute if score #bit {self.namespace}_temp matches 1 run function {self.namespace}:lib/sra_{amt}")
                lines.append(f"scoreboard players operation #amt {self.namespace}_temp /= #two {self.namespace}_const")
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f: f.write("\n".join(lines))
            if op == "srl":
                for i in range(5):
                    amt = 1 << i
                    with open(os.path.join(self.output_dir, "lib", f"srl_{amt}_neg.mcfunction"), 'w') as f:
                        lines_srl = [
                            f"scoreboard players operation #res {self.namespace}_temp -= #min_int {self.namespace}_const",
                            f"scoreboard players operation #res {self.namespace}_temp /= #p_{amt} {self.namespace}_const",
                            f"scoreboard players operation #res {self.namespace}_temp += #p_{31-amt} {self.namespace}_const"
                        ]
                        f.write("\n".join(lines_srl) + "\n")
            elif op == "sra":
                for i in range(5):
                    amt = 1 << i
                    with open(os.path.join(self.output_dir, "lib", f"sra_{amt}.mcfunction"), 'w') as f:
                        for _ in range(amt):
                            f.write(f"scoreboard players operation #old_res {self.namespace}_temp = #res {self.namespace}_temp\n")
                            f.write(f"scoreboard players operation #rem {self.namespace}_temp = #res {self.namespace}_temp\n")
                            f.write(f"scoreboard players operation #rem {self.namespace}_temp %= #two {self.namespace}_const\n")
                            f.write(f"scoreboard players operation #res {self.namespace}_temp /= #two {self.namespace}_const\n")
                            f.write(f"execute if score #old_res {self.namespace}_temp matches ..-1 if score #rem {self.namespace}_temp matches -1 run scoreboard players remove #res {self.namespace}_temp 1\n")

    def gen_mem(self):
        with open(os.path.join(self.output_dir, "mem", "init.mcfunction"), 'w') as f:
            f.write(f"data modify storage {self.namespace}:ram data set value [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]\n")
            # 16 * 2^18 = 4,194,304 words (16MB)
            for _ in range(18):
                f.write(f"data modify storage {self.namespace}:ram data append from storage {self.namespace}:ram data[]\n")
            
            f.write(f"data modify storage {self.namespace}:safe_ram data set value [0,0,0,0,0,0,0,0]\n")
            for _ in range(16):
                f.write(f"data modify storage {self.namespace}:safe_ram data append from storage {self.namespace}:safe_ram data[]\n")
            f.write(f"function {self.namespace}:lib/ascii/init_table\n")
            f.write(f"function {self.namespace}:lib/init_nbt_template\n")
            f.write(f"function {self.namespace}:lib/init_cmd_template\n")

        def gen_u_div(f, n):
            f.write(f"execute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp -= #min_int {self.namespace}_const\n")
            f.write(f"scoreboard players operation #w {self.namespace}_temp /= #p_{n} {self.namespace}_const\n")
            f.write(f"execute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp += #p_{31-n} {self.namespace}_const\n")

        with open(os.path.join(self.output_dir, "mem", "read_lb.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w {self.namespace}_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write(f"scoreboard players set #shift {self.namespace}_temp 0\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 1 run scoreboard players set #shift {self.namespace}_temp 8\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 3 run scoreboard players set #shift {self.namespace}_temp 24\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -3 run scoreboard players set #shift {self.namespace}_temp 8\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -1 run scoreboard players set #shift {self.namespace}_temp 24\n")
            
            f.write(f"execute unless score #off {self.namespace}_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write(f"scoreboard players operation #w {self.namespace}_temp %= #p_8 {self.namespace}_const\nexecute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp += #p_8 {self.namespace}_const\nexecute if score #w {self.namespace}_temp matches 128..255 run scoreboard players remove #w {self.namespace}_temp 256\nscoreboard players operation #res {self.namespace}_temp = #w {self.namespace}_temp\n")
        
        with open(os.path.join(self.output_dir, "mem", "u_div.mcfunction"), 'w') as f:
            f.write(f"execute if score #w {self.namespace}_temp matches ..-1 run scoreboard players set #is_neg {self.namespace}_temp 1\n")
            f.write(f"execute unless score #w {self.namespace}_temp matches ..-1 run scoreboard players set #is_neg {self.namespace}_temp 0\n")
            f.write(f"execute if score #is_neg {self.namespace}_temp matches 1 run scoreboard players operation #w {self.namespace}_temp -= #min_int {self.namespace}_const\n")
            
            f.write(f"execute if score #shift {self.namespace}_temp matches 8 run scoreboard players operation #w {self.namespace}_temp /= #p_8 {self.namespace}_const\n")
            f.write(f"execute if score #shift {self.namespace}_temp matches 16 run scoreboard players operation #w {self.namespace}_temp /= #p_16 {self.namespace}_const\n")
            f.write(f"execute if score #shift {self.namespace}_temp matches 24 run scoreboard players operation #w {self.namespace}_temp /= #p_24 {self.namespace}_const\n")
            
            f.write(f"execute if score #is_neg {self.namespace}_temp matches 1 if score #shift {self.namespace}_temp matches 8 run scoreboard players operation #w {self.namespace}_temp += #p_23 {self.namespace}_const\n")
            f.write(f"execute if score #is_neg {self.namespace}_temp matches 1 if score #shift {self.namespace}_temp matches 16 run scoreboard players operation #w {self.namespace}_temp += #p_15 {self.namespace}_const\n")
            f.write(f"execute if score #is_neg {self.namespace}_temp matches 1 if score #shift {self.namespace}_temp matches 24 run scoreboard players operation #w {self.namespace}_temp += #p_7 {self.namespace}_const\n")

        with open(os.path.join(self.output_dir, "mem", "read_lbu.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w {self.namespace}_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write(f"scoreboard players set #shift {self.namespace}_temp 0\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 1 run scoreboard players set #shift {self.namespace}_temp 8\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 3 run scoreboard players set #shift {self.namespace}_temp 24\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -3 run scoreboard players set #shift {self.namespace}_temp 8\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -1 run scoreboard players set #shift {self.namespace}_temp 24\n")
            f.write(f"execute unless score #off {self.namespace}_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write(f"scoreboard players operation #w {self.namespace}_temp %= #p_8 {self.namespace}_const\nexecute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp += #p_8 {self.namespace}_const\nscoreboard players operation #res {self.namespace}_temp = #w {self.namespace}_temp\n")
        
        with open(os.path.join(self.output_dir, "mem", "read_lh.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w {self.namespace}_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write(f"scoreboard players set #shift {self.namespace}_temp 0\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute unless score #off {self.namespace}_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write(f"scoreboard players operation #w {self.namespace}_temp %= #p_16 {self.namespace}_const\nexecute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp += #p_16 {self.namespace}_const\nexecute if score #w {self.namespace}_temp matches 32768..65535 run scoreboard players remove #w {self.namespace}_temp 65536\nscoreboard players operation #res {self.namespace}_temp = #w {self.namespace}_temp\n")
        
        with open(os.path.join(self.output_dir, "mem", "read_lhu.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w {self.namespace}_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write(f"scoreboard players set #shift {self.namespace}_temp 0\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute unless score #off {self.namespace}_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write(f"scoreboard players operation #w {self.namespace}_temp %= #p_16 {self.namespace}_const\nexecute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp += #p_16 {self.namespace}_const\nscoreboard players operation #res {self.namespace}_temp = #w {self.namespace}_temp\n")
        with open(os.path.join(self.output_dir, "mem", "read_lw.mcfunction"), 'w') as f:
             f.write(f"$execute store result score #res {self.namespace}_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
        with open(os.path.join(self.output_dir, "mem", "write_sw.mcfunction"), 'w') as f: f.write(f"$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")
        with open(os.path.join(self.output_dir, "mem", "write_sb.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #old {self.namespace}_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write(f"scoreboard players operation #w {self.namespace}_temp = #old {self.namespace}_temp\n")
            f.write(f"scoreboard players set #shift {self.namespace}_temp 0\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 1 run scoreboard players set #shift {self.namespace}_temp 8\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 3 run scoreboard players set #shift {self.namespace}_temp 24\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -3 run scoreboard players set #shift {self.namespace}_temp 8\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -1 run scoreboard players set #shift {self.namespace}_temp 24\n")
            f.write(f"execute unless score #off {self.namespace}_temp matches 0 run function {self.namespace}:mem/u_div\n")
            f.write(f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp\n")
            f.write(f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const\nexecute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const\n")
            f.write(f"scoreboard players set #mul {self.namespace}_const 1\nexecute if score #off {self.namespace}_temp matches 1 run scoreboard players operation #mul {self.namespace}_const = #p_8 {self.namespace}_const\nexecute if score #off {self.namespace}_temp matches 2 run scoreboard players operation #mul {self.namespace}_const = #p_16 {self.namespace}_const\nexecute if score #off {self.namespace}_temp matches 3 run scoreboard players operation #mul {self.namespace}_const = #p_24 {self.namespace}_const\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -3 run scoreboard players operation #mul {self.namespace}_const = #p_8 {self.namespace}_const\nexecute if score #off {self.namespace}_temp matches -2 run scoreboard players operation #mul {self.namespace}_const = #p_16 {self.namespace}_const\nexecute if score #off {self.namespace}_temp matches -1 run scoreboard players operation #mul {self.namespace}_const = #p_24 {self.namespace}_const\n")
            f.write(f"scoreboard players operation #byte {self.namespace}_temp *= #mul {self.namespace}_const\nscoreboard players operation #old {self.namespace}_temp -= #byte {self.namespace}_temp\nexecute store result score #new {self.namespace}_temp run data get storage {self.namespace}:io val\n")
            f.write(f"scoreboard players operation #new {self.namespace}_temp %= #p_8 {self.namespace}_const\nexecute if score #new {self.namespace}_temp matches ..-1 run scoreboard players operation #new {self.namespace}_temp += #p_8 {self.namespace}_const\nscoreboard players operation #new {self.namespace}_temp *= #mul {self.namespace}_const\n")
            f.write(f"scoreboard players operation #old {self.namespace}_temp += #new {self.namespace}_temp\nexecute store result storage {self.namespace}:io val int 1 run scoreboard players get #old {self.namespace}_temp\n$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")
        
        with open(os.path.join(self.output_dir, "mem", "write_sh.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #old {self.namespace}_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write(f"scoreboard players operation #w {self.namespace}_temp = #old {self.namespace}_temp\n")
            f.write(f"scoreboard players set #shift {self.namespace}_temp 0\n")
            f.write(f"execute if score #off {self.namespace}_temp matches 2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -2 run scoreboard players set #shift {self.namespace}_temp 16\n")
            f.write(f"execute unless score #off {self.namespace}_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write(f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp\n")
            f.write(f"scoreboard players operation #byte {self.namespace}_temp %= #p_16 {self.namespace}_const\nexecute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_16 {self.namespace}_const\n")
            f.write(f"scoreboard players set #mul {self.namespace}_const 1\nexecute if score #off {self.namespace}_temp matches 2 run scoreboard players operation #mul {self.namespace}_const = #p_16 {self.namespace}_const\n")
            f.write(f"execute if score #off {self.namespace}_temp matches -2 run scoreboard players operation #mul {self.namespace}_const = #p_16 {self.namespace}_const\n")
            f.write(f"scoreboard players operation #byte {self.namespace}_temp *= #mul {self.namespace}_const\nscoreboard players operation #old {self.namespace}_temp -= #byte {self.namespace}_temp\nexecute store result score #new {self.namespace}_temp run data get storage {self.namespace}:io val\n")
            f.write(f"scoreboard players operation #new {self.namespace}_temp %= #p_16 {self.namespace}_const\nexecute if score #new {self.namespace}_temp matches ..-1 run scoreboard players operation #new {self.namespace}_temp += #p_16 {self.namespace}_const\nscoreboard players operation #new {self.namespace}_temp *= #mul {self.namespace}_const\n")
            f.write(f"scoreboard players operation #old {self.namespace}_temp += #new {self.namespace}_temp\nexecute store result storage {self.namespace}:io val int 1 run scoreboard players get #old {self.namespace}_temp\n$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")

    def gen_read_nbt(self):
        lines = [
            f'data modify storage {self.namespace}:io_nbt buf set value ""',
            f'scoreboard players set #idx {self.namespace}_temp 0',
            f'scoreboard players operation #addr {self.namespace}_temp = x10 {self.namespace}_reg',
            f'function {self.namespace}:ecall/read_nbt_loop',
            f'data modify storage {self.namespace}:io_nbt source set from storage {self.namespace}:io_nbt buf',
            
            f'data modify storage {self.namespace}:io_nbt buf set value ""',
            f'scoreboard players set #idx {self.namespace}_temp 0',
            f'scoreboard players operation #addr {self.namespace}_temp = x11 {self.namespace}_reg',
            f'function {self.namespace}:ecall/read_nbt_loop',
            f'data modify storage {self.namespace}:io_nbt path set from storage {self.namespace}:io_nbt buf',
            
            f'function {self.namespace}:ecall/read_nbt_run_macro with storage {self.namespace}:io_nbt'
        ]
        with open(os.path.join(self.output_dir, "ecall", "read_nbt.mcfunction"), 'w') as f:
            f.write("\n".join(lines) + "\n")

        lines_loop = [
            f"execute if score #idx {self.namespace}_temp matches 256.. run return 0",
            
            f"scoreboard players operation #off {self.namespace}_temp = #addr {self.namespace}_temp",
            f"scoreboard players operation #off {self.namespace}_temp %= #four {self.namespace}_const",
            f"execute if score #off {self.namespace}_temp matches ..-1 run scoreboard players add #off {self.namespace}_temp 4",
            
            f"scoreboard players operation #addr_word {self.namespace}_temp = #addr {self.namespace}_temp",
            f"scoreboard players operation #addr_word {self.namespace}_temp /= #four {self.namespace}_const",
            
            f"execute store result storage {self.namespace}:io_nbt addr int 1 run scoreboard players get #addr_word {self.namespace}_temp",
            f"function {self.namespace}:mem/read_lw with storage {self.namespace}:io_nbt",
            f"scoreboard players operation #w {self.namespace}_temp = #res {self.namespace}_temp",
            
            f"scoreboard players set #valid {self.namespace}_temp 4",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #valid {self.namespace}_temp -= #off {self.namespace}_temp",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #op1 {self.namespace}_temp = #w {self.namespace}_temp",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #op2 {self.namespace}_temp = #off {self.namespace}_temp",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #op2 {self.namespace}_temp *= #p_3 {self.namespace}_const",
            f"execute if score #off {self.namespace}_temp matches 1.. run function {self.namespace}:lib/srl",
            f"execute if score #off {self.namespace}_temp matches 1.. run scoreboard players operation #w {self.namespace}_temp = #res {self.namespace}_temp",

            f"execute if score #valid {self.namespace}_temp matches ..0 run function {self.namespace}:ecall/read_nbt_next_word",
            f"execute if score #valid {self.namespace}_temp matches ..0 run return 0",
            
            f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp",
            f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches 0 run return 0",
            
            f"execute store result storage {self.namespace}:io_nbt char_idx int 1 run scoreboard players get #byte {self.namespace}_temp",
            f"function {self.namespace}:ecall/read_nbt_resolve_char with storage {self.namespace}:io_nbt",
            
            f"scoreboard players add #idx {self.namespace}_temp 1",
            f"scoreboard players remove #valid {self.namespace}_temp 1",

            f"execute if score #valid {self.namespace}_temp matches ..0 run function {self.namespace}:ecall/read_nbt_next_word",
            f"execute if score #valid {self.namespace}_temp matches ..0 run return 0",
            
            f"execute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp -= #min_int {self.namespace}_const",
            f"scoreboard players operation #w {self.namespace}_temp /= #p_8 {self.namespace}_const",
            f"execute if score #w {self.namespace}_temp matches ..-1 run scoreboard players operation #w {self.namespace}_temp += #p_23 {self.namespace}_const",
            
            f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp",
            f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches 0 run return 0",
            
            f"execute store result storage {self.namespace}:io_nbt char_idx int 1 run scoreboard players get #byte {self.namespace}_temp",
            f"function {self.namespace}:ecall/read_nbt_resolve_char with storage {self.namespace}:io_nbt",
            
            f"scoreboard players add #idx {self.namespace}_temp 1",
            f"scoreboard players remove #valid {self.namespace}_temp 1",

            f"execute if score #valid {self.namespace}_temp matches ..0 run function {self.namespace}:ecall/read_nbt_next_word",
            f"execute if score #valid {self.namespace}_temp matches ..0 run return 0",
            
            f"scoreboard players operation #w {self.namespace}_temp /= #p_8 {self.namespace}_const",
            f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp",
            f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches 0 run return 0",
            
            f"execute store result storage {self.namespace}:io_nbt char_idx int 1 run scoreboard players get #byte {self.namespace}_temp",
            f"function {self.namespace}:ecall/read_nbt_resolve_char with storage {self.namespace}:io_nbt",
            
            f"scoreboard players add #idx {self.namespace}_temp 1",
            f"scoreboard players remove #valid {self.namespace}_temp 1",

            f"execute if score #valid {self.namespace}_temp matches ..0 run function {self.namespace}:ecall/read_nbt_next_word",
            f"execute if score #valid {self.namespace}_temp matches ..0 run return 0",
            
            f"scoreboard players operation #w {self.namespace}_temp /= #p_8 {self.namespace}_const",
            f"scoreboard players operation #byte {self.namespace}_temp = #w {self.namespace}_temp",
            f"scoreboard players operation #byte {self.namespace}_temp %= #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches ..-1 run scoreboard players operation #byte {self.namespace}_temp += #p_8 {self.namespace}_const",
            f"execute if score #byte {self.namespace}_temp matches 0 run return 0",
            
            f"execute store result storage {self.namespace}:io_nbt char_idx int 1 run scoreboard players get #byte {self.namespace}_temp",
            f"function {self.namespace}:ecall/read_nbt_resolve_char with storage {self.namespace}:io_nbt",
            
            f"scoreboard players add #idx {self.namespace}_temp 1",

            f"function {self.namespace}:ecall/read_nbt_next_word"
        ]
        with open(os.path.join(self.output_dir, "ecall", "read_nbt_loop.mcfunction"), 'w') as f:
            f.write("\n".join(lines_loop) + "\n")
            
        with open(os.path.join(self.output_dir, "ecall", "read_nbt_next_word.mcfunction"), 'w') as f:
            lines_next = [
                f"scoreboard players operation #off {self.namespace}_temp = #addr {self.namespace}_temp",
                f"scoreboard players operation #off {self.namespace}_temp %= #four {self.namespace}_const",
                f"execute if score #off {self.namespace}_temp matches ..-1 run scoreboard players add #off {self.namespace}_temp 4",
                f"scoreboard players operation #next {self.namespace}_temp = #four {self.namespace}_const",
                f"scoreboard players operation #next {self.namespace}_temp -= #off {self.namespace}_temp",
                f"scoreboard players operation #addr {self.namespace}_temp += #next {self.namespace}_temp",
                f"function {self.namespace}:ecall/read_nbt_loop",
            ]
            f.write("\n".join(lines_next) + "\n")

        with open(os.path.join(self.output_dir, "ecall", "read_nbt_resolve_char.mcfunction"), 'w') as f:
            f.write(f"$data modify storage {self.namespace}:io_nbt char set from storage {self.namespace}:ascii table[$(char_idx)]\n")
            f.write(f"function {self.namespace}:ecall/read_nbt_append_char with storage {self.namespace}:io_nbt\n")

        with open(os.path.join(self.output_dir, "ecall", "read_nbt_append_char.mcfunction"), 'w') as f:
            f.write(f"$data modify storage {self.namespace}:io_nbt buf set value '$(buf)$(char)'\n")

        with open(os.path.join(self.output_dir, "ecall", "read_nbt_run_macro.mcfunction"), 'w') as f:
             f.write(f"$execute store result score x10 {self.namespace}_reg run data get storage $(source) $(path)\n")
    
    def gen_write_nbt(self):
        lines = [
            f'data modify storage {self.namespace}:io_nbt buf set value ""',
            f'scoreboard players set #idx {self.namespace}_temp 0',
            f'scoreboard players operation #addr {self.namespace}_temp = x10 {self.namespace}_reg',
            f'function {self.namespace}:ecall/read_nbt_loop',
            f'data modify storage {self.namespace}:io_nbt source set from storage {self.namespace}:io_nbt buf',

            f'data modify storage {self.namespace}:io_nbt buf set value ""',
            f'scoreboard players set #idx {self.namespace}_temp 0',
            f'scoreboard players operation #addr {self.namespace}_temp = x11 {self.namespace}_reg',
            f'function {self.namespace}:ecall/read_nbt_loop',
            f'data modify storage {self.namespace}:io_nbt path set from storage {self.namespace}:io_nbt buf',

            f'execute store result storage {self.namespace}:io_nbt value int 1 run scoreboard players get x12 {self.namespace}_reg',

            f'function {self.namespace}:ecall/write_nbt_run_macro with storage {self.namespace}:io_nbt'
        ]
        with open(os.path.join(self.output_dir, "ecall", "write_nbt.mcfunction"), 'w') as f:
            f.write("\n".join(lines) + "\n")

        with open(os.path.join(self.output_dir, "ecall", "write_nbt_run_macro.mcfunction"), 'w') as f:
             f.write("$data modify storage $(source) $(path) set value $(value)\n")

    def gen_ecall(self):
        with open(os.path.join(self.output_dir, "ecall", "dispatch.mcfunction"), 'w') as f:
            f.write(f"execute if score x17 {self.namespace}_reg matches 1 run function {self.namespace}:ecall/print_int\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 11 run function {self.namespace}:lib/uart_putc\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 12 run function {self.namespace}:ecall/syscon\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 13 run function {self.namespace}:ecall/load_data\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 14 run function {self.namespace}:ecall/exec_cmd_4096\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 15 run function {self.namespace}:ecall/read_nbt\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 16 run function {self.namespace}:ecall/write_nbt\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 18 run function {self.namespace}:ecall/exec_cmd_256\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 19 run function {self.namespace}:ecall/exec_cmd_512\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 20 run function {self.namespace}:ecall/exec_cmd_1024\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 21 run function {self.namespace}:ecall/exec_cmd_2048\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 22 run function {self.namespace}:ecall/exec_cmd_3072\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 23 run function {self.namespace}:ecall/screen_flush\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 24 run function {self.namespace}:ecall/screen_init\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 25 run function {self.namespace}:ecall/sleep\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 93 run function {self.namespace}:debug/dump_inline\n")
            f.write(f"execute if score x17 {self.namespace}_reg matches 10 run scoreboard players set #halt {self.namespace}_temp 1\n")
        
        with open(os.path.join(self.output_dir, "ecall", "load_data.mcfunction"), 'w') as f:
            f.write(f"scoreboard players operation #addr {self.namespace}_temp = x10 {self.namespace}_reg\n")
            f.write(f"scoreboard players operation #addr {self.namespace}_temp /= #four {self.namespace}_const\n")
            f.write(f"execute store result storage {self.namespace}:io dest_idx int 1 run scoreboard players get #addr {self.namespace}_temp\n")
            f.write(f'data modify storage {self.namespace}:io path set value "{self.namespace}:data"\n')
            f.write(f'data modify storage {self.namespace}:io nbt set value "Data"\n')
            f.write(f"function {self.namespace}:mem/copy_storage_to_ram with storage {self.namespace}:io\n")

        with open(os.path.join(self.output_dir, "ecall", "syscon.mcfunction"), 'w') as f:
            f.write(f'execute if score x10 {self.namespace}_reg matches 21845 run tellraw @a [{{"text":"[MC-RVVM] Powering Off.","color":"red"}}]\n')
            f.write(f"execute if score x10 {self.namespace}_reg matches 21845 run scoreboard players set #halt {self.namespace}_temp 1\n")
        with open(os.path.join(self.output_dir, "ecall", "print_int.mcfunction"), 'w') as f:
            f.write(f"tellraw @a [{{\"score\":{{\"name\":\"x10\",\"objective\":\"{self.namespace}_reg\"}},\"color\":\"green\"}}]\n")

    def gen_debug(self):
        with open(os.path.join(self.output_dir, "debug", "dump_inline.mcfunction"), 'w') as f:
            f.write(f"tellraw @a [{{\"text\":\"PC:\",\"color\":\"gray\"}},{{\"score\":{{\"name\":\"pc\",\"objective\":\"{self.namespace}_pc\"}}}},{{\"text\":\" | \",\"color\":\"dark_gray\"}}")
            for i in [1, 2, 8, 10, 11, 12, 13, 14, 15, 17]:
                f.write(f",{{\"text\":\"x{i}:\",\"color\":\"aqua\"}},{{\"score\":{{\"name\":\"x{i}\",\"objective\":\"{self.namespace}_reg\"}}}},{{\"text\":\" \",\"color\":\"white\"}}")
            f.write("]\n")