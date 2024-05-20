import tkinter as tk
from tkinter import Label, PhotoImage, ttk, messagebox
import mysql.connector

 
class Banco:
    def __init__(self):
        self.conexao = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='banco_tds0025'
        )
        self.cursor = self.conexao.cursor()
 
        self.usuarios = {}
        self.saldo = 0
        self.limite = 0
        self.chespecial = 0 # limite cheque especial
        self.extrato = ""
        self.numero_saques = 0
        self.LIMITE_SAQUES = 3
 
        self.criar_tabela_usuarios()
 
    def criar_tabela_usuarios(self):
        
        try:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(50) NOT NULL,
                cpf VARCHAR(11) UNIQUE NOT NULL,
                senha VARCHAR(50) NOT NULL,
                Saldo DOUBLE,
                ChequeEspecial DOUBLE                 
            )
            """)
            print("Tabela 'usuarios' criada com sucesso!")
        except mysql.connector.Error as err:
            print(f"Erro ao criar tabela: {err}")
 
        self.usuario_logado = False
 
    def login(self, cpf, senha):
        
        query = "SELECT * FROM usuarios WHERE cpf = %s AND senha = %s"
        valores = (cpf, senha)
 
        self.cursor.execute(query, valores)
        usuario = self.cursor.fetchone()
 
        if usuario:
            self.usuario_logado = True
            self.usuarios = {'cpf': usuario[2]}
            self.saldo = usuario[4]
            #self.chespecial = usuario[5]  # Atualiza o valor do cheque especial
            messagebox.showinfo("Login", "Login realizado com sucesso!")
            return True
        else:
            messagebox.showerror("Erro", "CPF ou senha incorretos.")
            return False
   
 
    def cadastrar_usuario(self, nome, cpf, senha, saldo):
       
        try:
            query = "INSERT INTO usuarios (nome, cpf, senha, Saldo, ChequeEspecial ) VALUES (%s, %s, %s, %s, %s)"
            self.limite = saldo*4 + saldo
            self.cheque = saldo*4
            valores = (nome, cpf, senha, saldo, self.cheque)
            self.cursor.execute(query, valores)
            self.conexao.commit()
            messagebox.showinfo("Cadastro", "Usuário cadastrado com sucesso!")
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao cadastrar usuário: {err}")
 
    def depositar(self, valor):

        if self.usuario_logado:
            if valor > 0:
                self.saldo += valor
                self.extrato += f"Depósito: R$ {valor:.2f}\n"
 
                query = "UPDATE usuarios SET Saldo = %s WHERE cpf = %s"
                valores = (self.saldo, self.usuarios.get('cpf'))
                try:
                    self.cursor.execute(query, valores)
                    self.conexao.commit()
                except mysql.connector.Error as err:
                    print(f"Erro ao atualizar saldo do usuário: {err}")
            else:
                messagebox.showerror("Erro", "Valor inválido.")
        else:
            messagebox.showerror("Erro", "Efetue o login para realizar o depósito.")
    
    def fExtrato(self):
        if self.usuario_logado:
            query = "SELECT Saldo, ChequeEspecial FROM usuarios WHERE cpf = %s"
            valores = (self.usuarios.get('cpf'),)
            try:
                self.cursor.execute(query, valores)
                saldo, chequeEspecial = self.cursor.fetchone()
                self.saldo = saldo
                self.chequeEspecial = chequeEspecial  # Atualiza o valor do cheque especial

                extrato = f"Saldo atual: R$ {saldo:.2f}\n"
                extrato += self.extrato  # Adiciona o extrato anterior
                print("\n================= Extrato ==================")
                print(extrato)
                print("============================================")
            except mysql.connector.Error as err:
                print(f"Erro ao obter extrato: {err}")


    def sacar(self, valor):
        if self.usuario_logado:
            if valor > 0:
                saldo_disponivel = self.saldo + self.chequeEspecial  # Corrigindo o nome da variável
                if valor > saldo_disponivel:
                    messagebox.showerror("Erro", "Valor de saque excede o saldo e o limite do cheque especial.")
                else:
                    if valor > self.saldo:
                        # Saque do cheque especial
                        self.chequeEspecial -= valor - self.saldo
                        self.saldo = 0
                    else:
                        # Saque do saldo normal
                        self.saldo -= valor

                    self.extrato += f"Saque: R$ {valor:.2f}\n"
                    self.numero_saques += 1

                    query = "UPDATE usuarios SET Saldo = %s, ChequeEspecial = %s WHERE cpf = %s"
                    valores = (self.saldo, self.chequeEspecial, self.usuarios.get('cpf'))
                    try:
                        self.cursor.execute(query, valores)
                        self.conexao.commit()
                        messagebox.showinfo("Saque", "Saque realizado com sucesso!")
                    except mysql.connector.Error as err:
                        print(f"Erro ao atualizar saldo do usuário: {err}")
            else:
                messagebox.showerror("Erro", "Valor de saque inválido.")
        else:
            messagebox.showerror("Erro", "Efetue o login para realizar o saque.")


    def sair(self):
        messagebox.showinfo("Sair", "Saindo do sistema.")
        self.conexao.close()
 
    def transferir(self, destino, valor):
        if self.usuario_logado:
            if valor > 0:
                saldo_disponivel = self.saldo + self.cheque  # Verifica o saldo total disponível (saldo + cheque especial)
                if valor > saldo_disponivel:
                    messagebox.showerror("Erro", "Valor da transferência excede o saldo e o limite do cheque especial.")
                else:
                    if valor > self.saldo:
                        # Calcula o valor restante para transferir do cheque especial
                        valor_restante = valor - self.saldo
                        self.saldo = 0
                        self.cheque -= valor_restante  # Atualiza o saldo do cheque especial
                        self.saldo -= valor_restante  # "Choque" do valor do cheque especial para o saldo
                    else:
                        self.saldo -= valor
                    self.extrato += f"Transferência: R$ {valor:.2f} para CPF: {destino}\n"
    
                    query = "UPDATE usuarios SET Saldo = %s, ChequeEspecial = %s WHERE cpf = %s"
                    valores = (self.saldo, self.cheque, self.usuarios.get('cpf'))
                    try:
                        self.cursor.execute(query, valores)
                        self.conexao.commit()
                        messagebox.showinfo("Transferência", f"Transferência de R$ {valor:.2f} realizada com sucesso para o CPF: {destino}.")
                    except mysql.connector.Error as err:
                        print(f"Erro ao atualizar saldo do usuário: {err}")
            else:
                messagebox.showerror("Erro", "Valor de transferência inválido.")
        else:
            messagebox.showerror("Erro", "Efetue o login para realizar a transferência.")




class Interface:
    
    def __init__(self, root, banco):
        self.banco = banco
        self.root = root
        self.banco = banco
        self.banco.interface = self
        self.root.title("CYBER BANK")
               
        style = ttk.Style()
        style.configure("TButton", foreground="black", background="#EDE3A1", font=("Century Gothic", 30, "bold"), borderwidth=2, relief="raised", padding=10)
        root.geometry("2000x2000")  # Define o tamanho da janela como 400x300 pixels


        # Adicionando imagens
        logo = PhotoImage(file="logo-removebg-preview.png")
        logo_label = Label(root, image=logo)
        logo_label.image = logo
        logo_label.configure(background="#0B294A")
        logo_label.pack(side="top", padx=10, pady=5,anchor="n",fill="none")
 
        # Adicionando botões
        
        button_logar = ttk.Button(root, text="Logar", command=self.logar)
        button_logar.pack(side="left",padx=5,pady=5,anchor="nw",fill="none",  )
 
        button_cadastrar = ttk.Button(root, text="Cadastrar", style="TButton", command=self.cadastrar)
        button_cadastrar.pack(side="left",padx=5, pady=5, anchor="w")    
 
        button_depositar = ttk.Button(root, text="Depositar", style="TButton", command=self.depositar)
        button_depositar.pack(side="left",padx=5, pady=5, anchor="nw" )

        button_sacar = ttk.Button(root, text="Sacar", style="TButton", command=self.sacar)
        button_sacar.pack(side="left",padx=5,pady=5,anchor="w")
 
        button_extrato = ttk.Button(root, text="Extrato", style="TButton", command=self.exibir_extrato)
        button_extrato.pack(side="left",padx=5, pady=5, anchor="nw")
 
        button_transferir = ttk.Button(root, text="Transferir", style="TButton", command=self.transferir)
        button_transferir.pack(side="left",padx=5,pady=5,anchor="w")
       
        button_sair = ttk.Button(root, text="Sair", style="TButton", command=self.sair)
        button_sair.pack(side="left", padx=5, pady=5 , anchor="nw")
 
       
    def logar(self):
        top = tk.Toplevel()
        top.geometry("300x150")
        top.title("Logar")
 
        tk.Label(top, text="CPF (apenas números):").pack()
        cpf_entry = tk.Entry(top)
        cpf_entry.pack()
 
        tk.Label(top, text="Senha:").pack()
        senha_entry = tk.Entry(top, show="*")
        senha_entry.pack()
 
        def logar():
            cpf = cpf_entry.get()
            senha = senha_entry.get()
 
            if cpf and senha:
                try:
                    self.banco.login(cpf, senha)
                    top.destroy()
                except Exception as e:
                    messagebox.showerror("Erro", str(e))
 
        tk.Button(top, text="Logar", command=logar).pack(side="top", padx= 10, pady=10, anchor="center")
 
    def cadastrar(self):
        top = tk.Toplevel()
        top.geometry("450x300")
        top.title("Cadastrar Usuário")
 
        tk.Label(top, text="Nome:").pack()
        nome_entry = tk.Entry(top)
        nome_entry.pack()
 
        tk.Label(top, text="CPF (apenas números):").pack()
        cpf_entry = tk.Entry(top)
        cpf_entry.pack()
 
        tk.Label(top, text="Senha:").pack()
        senha_entry = tk.Entry(top, show="*")
        senha_entry.pack()
 
        tk.Label(top, text="Saldo Inicial:").pack()
        saldo_entry = tk.Entry(top)
        saldo_entry.pack()
 
        def cadastrar_usuario():
            nome = nome_entry.get()
            cpf = cpf_entry.get()
            senha = senha_entry.get()
            saldo = float(saldo_entry.get())
 
            if nome and cpf and senha and saldo:
                try:
                    self.banco.cadastrar_usuario(nome, cpf, senha, saldo)
                    messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
                    top.destroy()
                except ValueError:
                    messagebox.showerror("Erro", "Saldo inválido. Por favor, insira um número válido.")
            else:
                messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
 
        tk.Button(top, text="Cadastrar", command=cadastrar_usuario).pack(side="top", padx=10,pady=10,anchor="center")
   
    def depositar(self):
        top = tk.Toplevel()
        top.geometry("200x150")
        top.title("Depositar")
 
        tk.Label(top, text="Valor do depósito:").pack()    
        valor_entry = tk.Entry(top)
        valor_entry.pack()
 
        def depositar():
            if self.banco.usuario_logado:
                valor = float(valor_entry.get())
                self.banco.depositar(valor)
                messagebox.showinfo("Depósito","Depositado com sucesso!")
                top.destroy()
            else:
                messagebox.showinfo("Erro", "Faça login primeiro para realizar um depósito.")
        tk.Button(top, text="Depositar", command=depositar).pack(side="top", padx=10,pady=10,anchor="center")
 
    def sacar(self):
        top = tk.Toplevel()
        top.geometry("200x150")
        top.title("Sacar")
 
        tk.Label(top, text="Valor do saque:").pack()
        valor_entry = tk.Entry(top)
        valor_entry.pack()
 
        def sacar():
            if self.banco.usuario_logado:
                valor = float(valor_entry.get())
                self.banco.sacar(valor)
                messagebox.showinfo("Saque","Saque realizado com sucesso!")
                top.destroy()
            else:
                messagebox.showinfo("Erro", "Faça login primeiro para realizar um saque.")
        tk.Button(top, text="Sacar", command=sacar).pack(side="top", padx=10,pady=10, anchor="center")
       
    def exibir_extrato(self):
        top = tk.Toplevel()
        top.geometry("600x400")
        top.title("Extrato")

        if self.banco.usuario_logado:
            self.banco.fExtrato()  # Chama o método para atualizar o saldo e obter o extrato
            # Exibição do saldo
            saldo_label = tk.Label(top, text=f"Saldo atual: R$ {self.banco.saldo:.2f}")
            saldo_label.pack()

            saldo_especialLabel = tk.Label(top, text=f"Cheque Especial: R$ {self.banco.chequeEspecial:.2f}")
            saldo_especialLabel.pack()

            # Exibição do extrato
            extrato_label = tk.Label(top, text="Extrato:")
            extrato_label.pack()

            extrato_text = tk.Text(top, height=10, width=50)
            extrato_text.pack()

            # Adiciona o extrato ao widget de texto
            extrato_text.insert(tk.END, self.banco.extrato)

            extrato_text.config(state=tk.DISABLED)  # Torna o widget somente leitura
        else:
            messagebox.showinfo("Erro", "Faça login primeiro para visualizar o extrato.")



 
    def sair(self):
        self.root.destroy()
 
    def exibir_interface_inicial(self):
        self.root.deiconify()
 
    def transferir(self):
        top = tk.Toplevel()
        top.geometry("500x500")
        top.title("Transferir")

        tk.Label(top, text="CPF do Destinatário (apenas números):").pack()
        cpf_destino_entry = tk.Entry(top)
        cpf_destino_entry.pack()

        tk.Label(top, text="Valor da Transferência:").pack()
        valor_entry = tk.Entry(top)
        valor_entry.pack()

        def transferir():
            cpf_destino = cpf_destino_entry.get()
            valor = float(valor_entry.get())

            if cpf_destino and valor:
                self.banco.transferir(cpf_destino, valor)
                top.destroy()
            else:
                messagebox.showerror("Erro", "Por favor, preencha todos os campos.")

        tk.Button(top, text="Transferir", command=transferir).pack(side="top", padx=10,pady=10, anchor="center")

 
# Criar a janela principal

root = tk.Tk()
root.configure(background="#0B294A")
interface = Interface(root, Banco())
root.mainloop()
