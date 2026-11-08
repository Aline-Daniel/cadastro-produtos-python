"""Interface desktop para cadastro de produtos."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from cadastro import Cadastro, formatar_preco


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cadastro Profissional de Produtos")
        self.geometry("1050x680")
        self.minsize(800, 540)
        self.configure(bg="#f3f6fa")
        self.db = Cadastro()
        self.selecionado = None
        self.campos = {}
        self.construir()
        self.atualizar_lista()

    def construir(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=29, background="white", fieldbackground="white", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#e3ebf5", foreground="#12223a", font=("Segoe UI", 10, "bold"))
        main = tk.Frame(self, bg="#f3f6fa", padx=25, pady=20)
        main.pack(fill="both", expand=True)
        tk.Label(main, text="Gerenciamento de produtos", font=("Segoe UI", 22, "bold"), bg="#f3f6fa", fg="#10203b").pack(anchor="w")
        tk.Label(main, text="Cadastre, edite, pesquise e exporte seus produtos com segurança.",
                 font=("Segoe UI", 10), bg="#f3f6fa", fg="#57677e").pack(anchor="w", pady=(0, 18))
        frame = tk.LabelFrame(main, text="  Dados do produto  ", bg="#ffffff", fg="#11253a", font=("Segoe UI", 11, "bold"), padx=16, pady=14)
        frame.pack(fill="x")
        labels = [("nome", "Nome"), ("valor", "Valor (R$)"), ("fornecedor", "Fornecedor"),
                  ("categoria", "Categoria"), ("responsavel", "Responsável pelo cadastro")]
        for i, (key, label) in enumerate(labels):
            row, col = divmod(i, 3)
            item = tk.Frame(frame, bg="white")
            item.grid(row=row, column=col, sticky="ew", padx=(0, 12), pady=7)
            frame.grid_columnconfigure(col, weight=1)
            tk.Label(item, text=label, anchor="w", bg="white", fg="#415369").pack(fill="x")
            entry = ttk.Entry(item, font=("Segoe UI", 11))
            entry.pack(fill="x", ipady=4, pady=(3, 0))
            self.campos[key] = entry
        toolbar = tk.Frame(main, bg="#f3f6fa", pady=14)
        toolbar.pack(fill="x")
        for title, callback in [("Salvar novo", self.salvar), ("Atualizar selecionado", self.editar),
                                ("Excluir selecionado", self.excluir), ("Limpar", self.limpar),
                                ("Exportar CSV (Excel)", self.exportar)]:
            tk.Button(toolbar, text=title, command=callback, bg="#24486e" if "Excluir" not in title else "#a02937",
                      fg="white", activebackground="#174779", padx=12, pady=9, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
        search = tk.Frame(main, bg="#f3f6fa")
        search.pack(fill="x", pady=(2, 10))
        tk.Label(search, text="Pesquisar nome, categoria, fornecedor ou responsável:", bg="#f3f6fa", fg="#24374e").pack(side="left", padx=(0, 10))
        self.busca = ttk.Entry(search, font=("Segoe UI", 11))
        self.busca.pack(side="left", fill="x", expand=True)
        self.busca.bind("<KeyRelease>", lambda _: self.atualizar_lista())
        columns = ("id", "nome", "valor", "fornecedor", "categoria", "responsavel")
        region = tk.Frame(main, bg="#f3f6fa")
        region.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(region, columns=columns, show="headings", selectmode="browse")
        for name, label, width in [("id", "ID", 55), ("nome", "Produto", 210), ("valor", "Valor", 90),
                                   ("fornecedor", "Fornecedor", 175), ("categoria", "Categoria", 150),
                                   ("responsavel", "Responsável", 180)]:
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, minwidth=50, stretch=name != "id")
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(region, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.selecionar)
        self.status = tk.Label(main, text="", bg="#f3f6fa", fg="#57677e", anchor="w")
        self.status.pack(fill="x", pady=8)

    def valores(self):
        return [self.campos[k].get() for k in ("nome", "valor", "fornecedor", "categoria", "responsavel")]

    def atualizar_lista(self):
        self.tree.delete(*self.tree.get_children())
        rows = self.db.listar(self.busca.get())
        for p in rows:
            self.tree.insert("", "end", iid=str(p["id"]), values=(p["id"], p["nome"],
                             formatar_preco(p["valor_centavos"]), p["fornecedor"], p["categoria"], p["responsavel"]))
        self.status.configure(text=f"{len(rows)} produto(s) exibido(s)")

    def selecionar(self, event=None):
        selection = self.tree.selection()
        if not selection: return
        self.selecionado = int(selection[0])
        values = self.tree.item(selection[0], "values")
        for key, v in zip(("nome", "valor", "fornecedor", "categoria", "responsavel"), values[1:]):
            self.campos[key].delete(0, tk.END)
            self.campos[key].insert(0, v)

    def limpar(self):
        for field in self.campos.values(): field.delete(0, tk.END)
        self.selecionado = None
        self.tree.selection_remove(self.tree.selection())

    def salvar(self):
        try:
            self.db.adicionar(*self.valores())
            self.atualizar_lista(); self.limpar()
            messagebox.showinfo("Sucesso", "Produto cadastrado.")
        except ValueError as e: messagebox.showerror("Verifique os dados", str(e))

    def editar(self):
        if self.selecionado is None: return messagebox.showwarning("Selecionar", "Escolha um produto na tabela.")
        try:
            self.db.atualizar(self.selecionado, *self.valores())
            self.atualizar_lista(); self.limpar()
            messagebox.showinfo("Sucesso", "Produto atualizado.")
        except ValueError as e: messagebox.showerror("Erro", str(e))

    def excluir(self):
        if self.selecionado is None: return messagebox.showwarning("Selecionar", "Escolha um produto na tabela.")
        if messagebox.askyesno("Confirmar exclusão", "Deseja excluir o produto selecionado?"):
            try:
                self.db.apagar(self.selecionado)
                self.atualizar_lista(); self.limpar()
            except ValueError as e: messagebox.showerror("Erro", str(e))

    def exportar(self):
        arquivo = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV (Excel)", "*.csv")], initialfile="produtos.csv")
        if arquivo:
            try:
                total = self.db.exportar_csv(Path(arquivo))
                messagebox.showinfo("Exportado", f"{total} produto(s) exportado(s) para CSV.")
            except OSError as e: messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    App().mainloop()
