"""
Scientific Calculator (Python + Tkinter)

Features:
  - Arithmetic: + - * / ** %  and parentheses
  - Trig (sin, cos, tan, asin, acos, atan) with Degree/Radian toggle
  - Hyperbolic (sinh, cosh, tanh), log (base 10), ln, sqrt, exp, abs, factorial
  - Constants: pi, e   |  Ans = previous result
  - Safe parsing (uses `ast`, never `eval`)
  - Keyboard support: Enter = evaluate, Esc = clear

Run:  python scientific_calculator.py
"""

import ast
import math
import operator
import tkinter as tk


# --------------------------------------------------------------------------
# Calculation engine (no GUI code here, so it is easy to test)
# --------------------------------------------------------------------------
class CalcError(Exception):
    pass


BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class Engine:
    def __init__(self):
        self.degrees = True
        self.ans = 0.0

    # --- angle helpers ---------------------------------------------------
    def _to_rad(self, x):
        return math.radians(x) if self.degrees else x

    def _from_rad(self, x):
        return math.degrees(x) if self.degrees else x

    def _functions(self):
        return {
            "sin": lambda x: math.sin(self._to_rad(x)),
            "cos": lambda x: math.cos(self._to_rad(x)),
            "tan": lambda x: math.tan(self._to_rad(x)),
            "asin": lambda x: self._from_rad(math.asin(x)),
            "acos": lambda x: self._from_rad(math.acos(x)),
            "atan": lambda x: self._from_rad(math.atan(x)),
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "log": math.log10,
            "ln": math.log,
            "sqrt": math.sqrt,
            "exp": math.exp,
            "abs": abs,
            "fact": self._factorial,
        }

    @staticmethod
    def _factorial(x):
        if x != int(x) or x < 0:
            raise CalcError("Factorial needs a non-negative integer")
        if x > 500:
            raise CalcError("Number too large for factorial")
        return math.factorial(int(x))

    # --- evaluation ------------------------------------------------------
    def evaluate(self, expression):
        expr = (
            expression.strip()
            .replace("×", "*")
            .replace("÷", "/")
            .replace("−", "-")
            .replace("^", "**")
            .replace("π", "pi")
            .replace("√", "sqrt")
        )
        if not expr:
            raise CalcError("Empty expression")
        try:
            tree = ast.parse(expr, mode="eval")
            result = self._eval(tree.body)
        except ZeroDivisionError:
            raise CalcError("Division by zero")
        except (ValueError, OverflowError) as exc:
            raise CalcError(f"Math error: {exc}")
        except SyntaxError:
            raise CalcError("Syntax error")
        self.ans = result
        return result

    def _eval(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.Name):
            consts = {"pi": math.pi, "e": math.e, "ans": self.ans}
            if node.id.lower() in consts:
                return consts[node.id.lower()]
            raise CalcError(f"Unknown name: {node.id}")

        if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
            left, right = self._eval(node.left), self._eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000 and abs(left) > 1:
                raise CalcError("Exponent too large")
            return BIN_OPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
            return UNARY_OPS[type(node.op)](self._eval(node.operand))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            funcs = self._functions()
            name = node.func.id.lower()
            if name not in funcs or node.keywords or len(node.args) != 1:
                raise CalcError(f"Bad function call: {node.func.id}")
            return funcs[name](self._eval(node.args[0]))

        raise CalcError("Unsupported expression")

    @staticmethod
    def format(value):
        if isinstance(value, complex):
            return str(value)
        if isinstance(value, float):
            if value.is_integer() and abs(value) < 1e15:
                return str(int(value))
            return f"{value:.12g}"
        return str(value)


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
class CalculatorApp:
    # (label, text inserted, style)
    LAYOUT = [
        [("Deg", None, "mode"), ("(", "(", "op"), (")", ")", "op"), ("C", None, "clear"), ("⌫", None, "clear")],
        [("sin", "sin(", "fn"), ("cos", "cos(", "fn"), ("tan", "tan(", "fn"), ("ln", "ln(", "fn"), ("log", "log(", "fn")],
        [("asin", "asin(", "fn"), ("acos", "acos(", "fn"), ("atan", "atan(", "fn"), ("√", "sqrt(", "fn"), ("n!", "fact(", "fn")],
        [("7", "7", "num"), ("8", "8", "num"), ("9", "9", "num"), ("÷", "/", "op"), ("^", "**", "op")],
        [("4", "4", "num"), ("5", "5", "num"), ("6", "6", "num"), ("×", "*", "op"), ("π", "pi", "fn")],
        [("1", "1", "num"), ("2", "2", "num"), ("3", "3", "num"), ("−", "-", "op"), ("e", "e", "fn")],
        [("0", "0", "num"), (".", ".", "num"), ("Ans", "ans", "fn"), ("+", "+", "op"), ("=", None, "equals")],
    ]

    COLORS = {
        "num": ("#2f3542", "#ffffff"),
        "op": ("#57606f", "#ffffff"),
        "fn": ("#3d4a5c", "#dfe6e9"),
        "clear": ("#c0392b", "#ffffff"),
        "equals": ("#27ae60", "#ffffff"),
        "mode": ("#8e44ad", "#ffffff"),
    }

    def __init__(self, root):
        self.root = root
        self.engine = Engine()
        root.title("Scientific Calculator")
        root.configure(bg="#1e272e")
        root.resizable(False, False)

        self.history_var = tk.StringVar()
        tk.Label(
            root, textvariable=self.history_var, anchor="e",
            bg="#1e272e", fg="#808e9b", font=("Consolas", 11),
        ).grid(row=0, column=0, columnspan=5, sticky="ew", padx=10, pady=(10, 0))

        self.entry = tk.Entry(
            root, font=("Consolas", 22), justify="right", bd=0,
            bg="#0f1419", fg="#ffffff", insertbackground="#ffffff",
        )
        self.entry.grid(row=1, column=0, columnspan=5, sticky="ew", padx=10, pady=8, ipady=10)
        self.entry.focus_set()

        self.mode_button = None
        for r, row in enumerate(self.LAYOUT, start=2):
            for c, (label, text, style) in enumerate(row):
                bg, fg = self.COLORS[style]
                btn = tk.Button(
                    root, text=label, width=6, height=2, bd=0,
                    font=("Segoe UI", 12, "bold"), bg=bg, fg=fg,
                    activebackground="#747d8c", activeforeground="#ffffff",
                    command=lambda l=label, t=text: self.on_press(l, t),
                )
                btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
                if label == "Deg":
                    self.mode_button = btn

        root.bind("<Return>", lambda _e: self.calculate())
        root.bind("<KP_Enter>", lambda _e: self.calculate())
        root.bind("<Escape>", lambda _e: self.clear())

    def on_press(self, label, text):
        if label == "=":
            self.calculate()
        elif label == "C":
            self.clear()
        elif label == "⌫":
            current = self.entry.get()
            self.entry.delete(0, tk.END)
            self.entry.insert(0, current[:-1])
        elif label in ("Deg", "Rad"):
            self.engine.degrees = not self.engine.degrees
            self.mode_button.config(text="Deg" if self.engine.degrees else "Rad")
        else:
            self.entry.insert(tk.END, text)
        self.entry.focus_set()

    def clear(self):
        self.entry.delete(0, tk.END)
        self.history_var.set("")

    def calculate(self):
        expression = self.entry.get()
        try:
            result = self.engine.format(self.engine.evaluate(expression))
        except CalcError as exc:
            self.history_var.set(str(exc))
            return
        self.history_var.set(f"{expression} =")
        self.entry.delete(0, tk.END)
        self.entry.insert(0, result)


def main():
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()