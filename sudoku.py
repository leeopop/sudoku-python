#!/usr/env/python
from collections import defaultdict
import itertools

cell_size = 100
cell_margin = 10
class Cell:
    def __init__(self, board, key, value=0):
        if value == 0:
            self.possible = set(range(1, 10))
            self.impossible = set()
        else:
            self.possible = set([value])
            self.impossible = set(range(1, 10))
            self.impossible.remove(value)
        self.board = board
        self.value = value
        self.key = key

        if self.board.canvas is not None:
            row, col = key
            pos_x = col*cell_size
            pos_y = row*cell_size
            self.board.canvas.create_rectangle(pos_x, pos_y, pos_x + cell_size, pos_y + cell_size)
            obj = self.board.canvas.create_rectangle(pos_x, pos_y, pos_x + cell_size, pos_y + cell_size, fill="lightblue")
            self.board.canvas_units[key] = obj
            self.possible_text = self.board.canvas.create_text(pos_x+cell_margin, pos_y+1*cell_margin, fill="blue", text="possibles", anchor="nw", font=('Times', 10), width=cell_size-2*cell_margin)
            self.board.canvas.itemconfigure(self.possible_text, state="normal")
            self.impossible_text = self.board.canvas.create_text(pos_x+cell_margin, pos_y+3*cell_margin, fill="red", text="impossibles", anchor="nw", font=('Times', 10), width=cell_size-2*cell_margin)
            self.board.canvas.itemconfigure(self.impossible_text, state="normal")
            self.known_text = self.board.canvas.create_text(pos_x+cell_size/2, pos_y+cell_size/2, fill="black", text="known", anchor="center", font=('Times', 24), width=cell_size-2*cell_margin)
            self.board.canvas.itemconfigure(self.known_text, state="hidden")
            obj = self.board.canvas.create_text(pos_x+cell_margin, pos_y+6.5*cell_margin, fill="purple", text="interest", anchor="nw", font=('Times', 10), width=cell_size-2*cell_margin)
            self.board.canvas_interests[key] = obj
    pass

    def update_text(self):
        if self.board.canvas is not None:
            if self.value != 0:
                self.board.canvas.itemconfigure(self.known_text, state="normal", text=str(self.value))
                self.board.canvas.itemconfigure(self.possible_text, state="hidden")
                self.board.canvas.itemconfigure(self.impossible_text, state="hidden")
            else:
                possible_list = list(self.possible)
                possible_list.sort()
                impossible_list = list(self.impossible)
                impossible_list.sort()
                self.board.canvas.itemconfigure(self.known_text, state="hidden")
                self.board.canvas.itemconfigure(self.possible_text, state="normal",text=" ".join(map(str, possible_list)))
                self.board.canvas.itemconfigure(self.impossible_text, state="normal",text=" ".join(map(str, impossible_list)))

    def copy(self, new_board):
        new_cell = Cell(new_board, self.key, self.value)
        new_cell.possible = set(self.possible.copy())
        new_cell.impossible = set(self.impossible.copy())
        return new_cell

    def remove_possible(self, value=int or set(int)):
        ret = False
        if isinstance(value, set):
            to_remove = value.intersection(self.possible)
            if len(to_remove) > 0:
                self.possible = self.possible.difference(to_remove)
                self.impossible = self.impossible.union(to_remove)
                ret = True
        elif isinstance(value, int):
            if value in self.possible:
                self.possible.remove(value)
                self.impossible.add(value)
                ret = True
        else:
            raise Exception("Invalid type for value")
        if ret:
            self.board.mark_changed(self.key)
            self.update_text()
        assert len(self.possible) + len(self.impossible) == 9
        assert len(self.possible.intersection(self.impossible)) == 0
        if len(self.possible) == 0:
            raise Exception("No possible value at cell %s" % str(self.key))
        return ret

    def set_value(self, value=int):
        if self.value == value:
            ret = False
        else:
            ret = True
        self.possible = set([value])
        self.impossible = set(range(1, 10))
        self.impossible.remove(value)
        self.value = value
        if ret:
            self.board.known_cells[self.key] = self.board.unknown_cells.pop(self.key)
            self.board.mark_changed(self.key)
            for unit_key in self.get_unit_keys():
                for cell_key in self.board.get_unsolved_unit_cell_keys(unit_key):
                    if cell_key == self.key:
                        continue
                    cell = self.board.get_cell(cell_key)
                    cell.remove_possible(value)
            self.update_text()
        return ret
    
    def get_row_key(self):
        (row, col) = self.key
        return (-row, 0)
    
    def get_col_key(self):
        (row, col) = self.key
        return (0, -col)
    
    def get_rect_key(self):
        (row, col) = self.key
        return (-((row-1)//3)-1, -((col-1)//3)-1)
    
    def get_unit_keys(self):
        return [self.get_row_key(), self.get_col_key(), self.get_rect_key()]

class Sudoku:
    def __init__(self, init=True):
        self.canvas = None
        self.canvas_units = dict()
        self.canvas_interests = dict()
        self.do_print = True
        self.set_single_in_progress = None
        self.all_cells = dict()
        self.known_cells = dict()
        self.unknown_cells = dict()
        self.changed = set()
        self.wait_user = False
        if init:
            try:
                import tkinter
                self.canvas = tkinter.Canvas(width=1024, height=1024)
                for row in range(3):
                    for col in range(3):
                        key = (-row-1, -col-1)
                        rect_size = cell_size * 3
                        pos_x = col * rect_size + cell_size
                        pox_y = row * rect_size + cell_size
                        self.canvas.create_rectangle(pos_x, pox_y, pos_x + rect_size, pox_y + rect_size, outline="black", width=3) # Won't be changed
                        obj = self.canvas.create_rectangle(pos_x, pox_y, pos_x + rect_size, pox_y + rect_size, state="hidden", fill="lightblue", width=5, outline="purple")
                        self.canvas_units[key] = obj
                for row in range(1, 10):
                    key = (-row, 0)
                    pos_x = cell_size
                    pox_y = row * cell_size
                    obj = self.canvas.create_rectangle(pos_x, pox_y, pos_x + cell_size*9, pox_y + cell_size, state="hidden", fill="lightblue", width=5, outline="purple")
                    self.canvas_units[key] = obj
                for col in range(1, 10):
                    key = (0, -col)
                    pos_x = col * cell_size
                    pox_y = cell_size
                    obj = self.canvas.create_rectangle(pos_x, pox_y, pos_x + cell_size, pox_y + cell_size*9, state="hidden", fill="lightblue", width=5, outline="purple")
                    self.canvas_units[key] = obj
                self.canvas.pack()
            except:
                pass
            for row in range(1, 10):
                for col in range(1, 10):
                    key = (row, col)
                    cell = Cell(self, key)
                    self.all_cells[key] = cell
                    self.unknown_cells[key] = cell
                
                for row in range(1,10):
                    for col in range(1,10):
                        key = (row, col)

        self.updated_cells = set() # to compare with new updates
        
        # try:
        #     import tkinter
        #     self.gui = tkinter.Tk()
        # except:
        #     self.gui = None
    
    def clear_marks(self):
        self.updated_cells.clear()
        if self.canvas:
            for obj in self.canvas_units.values():
                self.canvas.itemconfigure(obj, state="hidden")
            for obj in self.canvas_interests.values():
                self.canvas.itemconfigure(obj, state="hidden")

    def mark_changed(self, cell_key):
        self.changed.add(cell_key)
        self.updated_cells.add(cell_key)
        
    
    def wait_for_next_setep(self, used_group=None, interest_cells=set(), interest_values=set(), interest_name=""):
        if self.wait_user and self.canvas is not None:
            if len(interest_cells) > 0 and len(interest_values)>0:
                if len(interest_name) > 0:
                    text = "{}:\n".format(interest_name)
                else:
                    text = ""
                values = list(interest_values)
                values.sort()
                text += " ".join(map(str, values))
                for key in interest_cells:
                    self.canvas.itemconfigure(self.canvas_interests[key], state="normal", text=text)
            changed_and_used = self.updated_cells.intersection(interest_cells)
            changed_not_used = self.updated_cells.difference(interest_cells)
            for key in changed_and_used:
                self.canvas.itemconfigure(self.canvas_units[key], state="normal", fill="mediumpurple")
            for key in changed_not_used:
                self.canvas.itemconfigure(self.canvas_units[key], state="normal", fill="pink")
            if used_group is not None:
                self.canvas.itemconfigure(self.canvas_units[used_group], state="normal")
            self.print_current()
            input()
        self.clear_marks()
    
    # def all_cells(self):
    #     return self.all_cells.values()
    
    # def known_cells(self):
    #     return self.known_cells.values()
    
    def take_unknown_keys(self):
        return set(self.unknown_cells.keys())

    # 변경된 cell 좌표 가져오기
    def take_changed(self):
        prev = self.changed
        self.changed = set()
        return prev

    # Peek changed
    def peek_changed(self):
        return set(self.changed)
    
    def set_cell(self, key, value):
        if key in self.unknown_cells:
            if self.unknown_cells[key].set_value(value):
                return True
        return False

    def is_row_index(self, row_key):
        (row, col) = row_key
        assert (-row) in range(1, 10)
        col == 0 and row < 0

    def is_col_index(self, col_key):
        (row, col) = col_key
        assert (-col) in range(1, 10)
        row == 0 and col < 0
    
    def is_rect_index(self, rect_key):
        (row, col) = rect_key
        assert (-row) in range(1, 4) and (-col) in range(1, 4)
        row < 0 and col < 0

    def is_cell_index(self, cell_key):
        (row, col) = cell_key
        assert row in range(1, 10) and col in range(1, 10)
        row > 0 and col > 0
    
    def get_cell(self, key):
        if key in self.all_cells:
            return self.all_cells[key]
        return None
    
    # 어떤 종류의 유닛이던 간에 그 item 을 리턴한다
    def _get_unit_cell_keys(self, unit_key, base_cells):
        (row, col) = unit_key
        if row == 0 and col == 0:
            raise Exception("Invalid unit key")
        elif row == 0:
            # col
            for row in range(1, 10):
                if (row, -col) in base_cells:
                    yield (row, -col)
            return
        elif col == 0:
            # row
            for col in range(1, 10):
                if (-row, col) in base_cells:
                    yield (-row, col)
            return
        else:
            # rect
            for row_idx in range(1, 4):
                for col_idx in range(1, 4):
                    new_row = (-row-1)*3 + row_idx
                    new_col = (-col-1)*3 + col_idx
                    if (new_row, new_col) in base_cells:
                        yield (new_row, new_col)
            return
    
    # 어떤 종류의 유닛이던 간에 그 item 을 리턴한다
    def _get_unit_string(self, unit_key):
        (row, col) = unit_key
        if row == 0 and col == 0:
            raise Exception("Invalid unit key")
        elif row == 0:
            # col
            return "col %d" % (-col)
        elif col == 0:
            # row
            return "row %d" % (-row)
        else:
            # rect
            return "rect %d %d" % (-row, -col)
    # 어떤 종류의 유닛이던 간에 그 item 을 리턴한다
    def get_unsolved_unit_cell_keys(self, unit_key):
        for x in self._get_unit_cell_keys(unit_key, self.unknown_cells):
            yield x

    # Cell 의 possible 이 1개인지 검사한다.
    # 이 외 작업은 수행하지 않는다.
    def solve_unique(self, cell_keys=None):
        if cell_keys is None:
            cell_keys = map(self.unknown_cells.values(), lambda x: x.key)
        updated_once = False
        for cell_key in cell_keys:
            cell = self.get_cell(cell_key)
            if len(cell.possible) == 1:
                value = list(cell.possible)[0]
                if self.set_cell(cell.key, value):
                    self.print("unique possiblity in a cell", cell.key, value)
                    updated_once = True
                    self.wait_for_next_setep(interest_cells=[cell_key], interest_name="Uniq(Cell)", interest_values=[value])
        return updated_once
    
    # 각 unit 에서 유일하게 한번 가능한 것을 확정시킴
    def solve_unique_unit(self, unit_keys):
        updated_once = False
        for unit_key in unit_keys:
            updated = False
            count_dict = defaultdict(list)
            for cell_key in self.get_unsolved_unit_cell_keys(unit_key):
                cell = self.get_cell(cell_key)
                for possible in cell.possible:
                    count_dict[possible].append(cell.key)
            print_args = []
            interest_cells = set()
            for possible, keys in count_dict.items():
                if len(keys) == 1:
                    print_args.append((keys[0], possible))
                    if self.set_cell(keys[0], possible):
                        interest_cells.add(keys[0])
                        self.wait_for_next_setep(used_group=unit_key, interest_cells=keys, interest_name="Uniq(Unit)", interest_values=[possible])
                        
                        updated_once = True
                        updated = True
            if updated:
                self.print("unique possiblity in a unit", self._get_unit_string(unit_key))
                for key, possible in print_args:
                    self.print("\t", key, possible)
        return updated_once
    
    def set_print(self, flag=True):
        self.do_print = flag
    
    def set_wait_user(self, flag=True):
        self.wait_user = flag
    
    def print(self, *args, **kwargs):
        if self.do_print:
            print(*args, **kwargs)
    
    def solve_subsection(self, unit_keys):
        updated_once = False
        for unit_key in unit_keys:
            unsolved_items = list(self.get_unsolved_unit_cell_keys(unit_key))
            
            all_possibles = set()
            for cell_key in unsolved_items:
                cell = self.get_cell(cell_key)
                all_possibles = all_possibles.union(cell.possible)
            for select_count in range(2, 5):
                while True:
                    updated = False
                    if select_count < len(unsolved_items):
                        # Naked subsets
                        for selected in itertools.combinations(unsolved_items, select_count):
                            possible_set = set()
                            for cell_key in selected:
                                cell = self.get_cell(cell_key)
                                possible_set = possible_set.union(cell.possible)
                            if len(possible_set) == select_count:
                                removed_list = []
                                for cell_key in unsolved_items:
                                    if cell_key not in selected:
                                        cell = self.get_cell(cell_key)
                                        if cell.remove_possible(possible_set):
                                            removed_list.append(cell_key)
                                            updated_once = True
                                            updated = True
                                if len(removed_list) > 0:
                                    self.print("Naked subset: possible union set of %s is %s" % (str(selected), str(possible_set)))
                                    for cell_key in removed_list:
                                        self.print("\tRemoving from others(%s)" % (str(cell_key)))
                                    self.wait_for_next_setep(used_group=unit_key, interest_cells=selected, interest_name="Naked({})".format(select_count), interest_values=possible_set)
                    if not updated:
                        break
                    if updated:
                        return True
                while True:
                    updated = False
                    if select_count < len(all_possibles):
                        # Hidden subsets
                        for selected in itertools.combinations(all_possibles, select_count):
                            cell_with_selected = set()
                            selected = set(selected)
                            for cell_key in unsolved_items:
                                cell = self.get_cell(cell_key)
                                if len(selected.intersection(cell.possible)) > 0:
                                    cell_with_selected.add(cell_key)
                            if len(cell_with_selected) == select_count:
                                removed_list = []
                                for cell_key in cell_with_selected:
                                    cell = self.get_cell(cell_key)
                                    removing = cell.possible.difference(selected)
                                    if cell.remove_possible(removing):
                                        removed_list.append((cell_key, removing))
                                        updated_once = True
                                        updated = True
                                if len(removed_list) > 0:
                                    self.print("Hidden subset: values %s exists only in %s" % (str(selected), str(cell_with_selected)))
                                    for (cell_key, removing) in removed_list:
                                        self.print("\tRemoving %s from %s" % (str(removing), str(cell_key)))
                                    self.wait_for_next_setep(used_group=unit_key, interest_cells=cell_with_selected, interest_name="Hidden({})".format(select_count), interest_values=selected)
                    if not updated:
                        break
                    if updated:
                        return True;
        return updated_once
    
    def solve(self, recursion=True):
        unit_updated = set()

        while True:
            unknown = self.take_unknown_keys()
            updated_once = False
            unit_updated = unit_updated.union(unknown)
            if self.solve_unique(unknown):
                updated_once = True
                continue
            all_units = set()
            for updated_key in unknown:
                for k in self.get_cell(updated_key).get_unit_keys():
                    all_units.add(k)
            if self.solve_unique_unit(all_units):
                updated_once = True
                continue
            if self.solve_subsection(all_units):
                updated_once = True
                continue
            if not updated_once and recursion:
                before_sort = self.unknown_cells.items()
                before_sort = sorted(before_sort, key=lambda x: len(x[1].possible))
                sorted_keys = list(map(lambda x: x[0], before_sort))
                for cell_key in sorted_keys: # self.unknown_cells.keys():
                    fatal = []
                    target_cell = self.get_cell(cell_key)
                    possibles = target_cell.possible
                    # if len(possibles) != 2:
                    #     continue
                    clones = []
                    for possible in possibles:
                        clone = self.copy()
                        clone.set_print(False)
                        try:
                            clone.set_cell(cell_key, possible)
                            clone.solve(recursion=False)
                        except Exception as e:
                            fatal.append((cell_key, possible, str(e)))
                            continue
                        clones.append(clone)
                    new_impossibles = []
                    for check_key in self.unknown_cells.keys():
                        if check_key == cell_key:
                            continue
                        intersect = None
                        for clone in clones:
                            cell = clone.get_cell(check_key)
                            this_intersect = cell.impossible.difference(self.get_cell(cell_key).impossible)
                            if intersect is None:
                                intersect = this_intersect
                            else:
                                intersect = intersect.intersection(this_intersect)
                        if intersect is not None and len(intersect) > 0:
                            new_impossibles.append((check_key, intersect))
                    if len(new_impossibles) > 0 or len(fatal) > 0:
                        self.print("For any possible value from", cell_key, possibles)
                    for (cell_key, val, msg) in fatal:
                        self.print("\tAssuming %s as %d causes %s" % (str(cell_key), val, msg))
                    for check_key, intersect in new_impossibles:
                        cell = self.get_cell(check_key)
                        self.print("\tImpossible", check_key, intersect)
                        if cell.remove_possible(intersect):
                            updated_once = True
                            break
                        self.wait_for_next_setep()
                    if updated_once:
                        break
            if not updated_once:
                break
    
    def print_current(self):
        for i in range(1, 10):
            for j in range(1, 10):
                if (i, j) in self.known_cells:
                    self.print(self.known_cells[(i,j)].value,sep="", end=" ")
                else:
                    self.print("-", sep="", end=" ")
            self.print()
        pass

    def copy(self):
        ret = Sudoku(init=False)
        for key, cell in self.all_cells.items():
            ret.all_cells[key] = cell.copy(ret)
        for key, cell in self.known_cells.items():
            ret.known_cells[key] = ret.all_cells[key]
        for key, cell in self.unknown_cells.items():
            ret.unknown_cells[key] = ret.all_cells[key]
        return ret


def main():
#     # Easy
#     text = """
# 000904600
# 040000831
# 820610000
# 090832107
# 218745000
# 703006000
# 002000400
# 185429060
# 370000020
# """
#     # Expert
#     text = """
# 080001069
# 000000000
# 016400000
# 004206000
# 000130000
# 000000802
# 038000000
# 040007050
# 000029047
# """
#     # Master
#     text = """
# 090005000
# 400000800
# 008203060
# 000090000
# 070000001
# 004608030
# 002050000
# 000040090
# 100902003
# """

# # Wiki-17
#     text = """
# 000000010
# 000002003
# 000400000
# 000000500
# 401600000
# 007100000
# 050000200
# 000080040
# 030910000
# """

# # Namu - Naked 4
#     text = """
# 036820005
# 580034000
# 190000000
# 020900000
# 900306002
# 000002050
# 000000046
# 000680093
# 600090520
# """
# # Namu - Hidden 2
#     text = """
# 000000000
# 904607000
# 076804100
# 309701080
# 708000301
# 051308702
# 007502610
# 005403208
# 000070000
# """

# # Namu - Hidden 4
#     text = """
# 027605930
# 000000002
# 003280500
# 758136294
# 030804000
# 140502803
# 001020600
# 380061020
# 060758319
# """

    sudoku = Sudoku()
    sudoku.set_print(False)
    index = 0
    while index < 9*9:
        text = input()
        for x in text:
            if x not in "0123456789":
                continue
            col = index % 9 + 1
            row = index // 9 + 1
            val = int(x)
            if val > 0:
                sudoku.set_cell((row, col), val)
            index += 1
    
    print("Done input")
    sudoku.solve_unique(sudoku.peek_changed())
    sudoku.set_print(True)
    sudoku.set_wait_user(True)
    sudoku.wait_for_next_setep()
    sudoku.solve(recursion=True)
    sudoku.wait_for_next_setep()
    pass

if __name__ == '__main__':
    main()
