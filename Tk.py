import tkinter as tk
from tkinter import Label, PhotoImage, ttk, messagebox
import firebase_admin
from firebase_admin import credentials, db
import tkinter.simpledialog
import json

cred_obj = credentials.Certificate("C:\\Users\\964030\\Documents\\GitHub\\banoVfinal\\cyberbank-398fd-default-rtdb-export (1).json")
  
firebase_admin.initialize_app(cred_obj, {
    'databaseURL': 'https://cyberbank-398fd-default-rtdb.firebaseio.com/'
})

#ref = db.reference('/')

class Banco:
    def __init__(self):
        self.usuarios_ref = db.reference('usuarios')
        self.usuario_logado = False
        self.usuarios = {}
        self.saldo = 0
        self.limite = 0
        self.chespecial = 0  # limite cheque especial
        self.extrato = ""
        self.numero_saques = 0
        self.LIMITE_SAQUES = 3
        self.chequeI = 0

    def login(self, cpf, senha):
        usuario_ref = self.usuarios_ref.child(cpf)
        usuario = usuario_ref.get()

        if usuario and usuario['senha'] == senha:
            self.usuario_logado = True
            self.usuarios = {'CPF': cpf}
            self.saldo = usuario['Saldo']
            self.chespecial = usuario['chequeEspecial']
            self.chequeI = usuario['chequeI']
            messagebox.showinfo("Login", "Login realizado com sucesso!")
            return True
        else:
            messagebox.showerror("Erro", "CPF ou senha incorretos.")
            return False

    def cadastrar_usuario(self, nome, cpf, senha, saldo):
        try:
            self.chequeI = saldo * 4
            self.limite = saldo * 4 + saldo
            self.chespecial = saldo * 4
            usuario_data = {
                'nome': nome,
                'CPF': cpf,
                'senha': senha,
                'Saldo': saldo,
                'chequeEspecial': self.chespecial,
                'chequeI': self.chequeI
            }
            self.usuarios_ref.child(cpf).set(usuario_data)
            messagebox.showinfo("Cadastro", "Usuário cadastrado com sucesso!")
        except Exception as err:
            messagebox.showerror("Erro", f"Erro ao cadastrar usuário: {err}")

    def depositar(self, valor):
        if self.usuario_logado:
            if valor > 0:
                if self.chespecial < self.chequeI:
                    diferenca = self.chequeI - self.chespecial
                    if valor > diferenca:
                        self.saldo += valor 
                        self.chespecial += diferenca
                    else:
                        self.chespecial += valor
                        self.saldo += valor
                else:
                    self.saldo += valor

                self.extrato += f"Depósito: R$ {valor:.2f}\n"
                self.atualizar_usuario()
            else:
                messagebox.showerror("Erro", "Valor inválido.")
        else:
            messagebox.showerror("Erro", "Efetue o login para realizar o depósito.")

    def fExtrato(self):
        if self.usuario_logado:
            usuario_ref = self.usuarios_ref.child(self.usuarios.get('CPF'))
            usuario = usuario_ref.get()
            if usuario:
                self.saldo = usuario['Saldo']
                self.chespecial = usuario['chequeEspecial']

                extrato = f"Saldo atual: R$ {self.saldo:.2f}\n"
                extrato += f"Cheque Especial disponível: R$ {self.chespecial:.2f}\n"
                extrato += self.extrato
                print("\n================= Extrato ==================")
                print(extrato)
                print("============================================")
            else:
                print("Erro ao obter extrato")

    def sacar(self, valor):
        if self.usuario_logado:
            if valor > 0:
                if self.saldo < 0:
                    saldo_disponivel = self.chespecial
                else:
                    saldo_disponivel = self.saldo + self.chespecial
                if valor > saldo_disponivel:
                    messagebox.showerror("Erro", "Valor de saque excede o saldo e o limite do cheque especial.")
                else:
                    if valor > self.saldo:
                        if self.saldo < 0:
                            self.saldo -= valor
                            self.chespecial -= valor
                        else:
                            diferenca = valor - self.saldo
                            self.chespecial -= diferenca
                            self.saldo -= valor
                    else:
                        self.saldo -= valor

                    self.extrato += f"Saque: R$ {valor:.2f}\n"
                    self.numero_saques += 1
                    self.atualizar_usuario()
                    messagebox.showinfo("Saque", "Saque realizado com sucesso!")
            else:
                messagebox.showerror("Erro", "Valor de saque inválido.")
        else:
            messagebox.showerror("Erro", "Efetue o login para realizar o saque.")

    def sair(self):
        messagebox.showinfo("Sair", "Saindo do sistema.")
        # Não é necessário fechar a conexão com o Firebase como é com MySQL

    def transferir(self, destino, valor):
        if self.usuario_logado:
            try:
                valor = float(valor)
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido.")
                return
            if valor > 0:
                if self.saldo < 0:
                    saldo_disponivel = self.chespecial
                else:
                    saldo_disponivel = self.saldo + self.chespecial
                if valor > saldo_disponivel:
                    messagebox.showerror("Erro", "Valor de saque excede o saldo e o limite do cheque especial.")
                else:
                    if valor > self.saldo:
                        if self.saldo < 0:
                            self.saldo -= valor
                            self.chespecial -= valor
                        else:
                            diferenca = valor - self.saldo
                            self.chespecial -= diferenca
                            self.saldo -= valor
                    else:
                        self.saldo -= valor
                    self.extrato += f"Transferência: R$ {valor:.2f} para CPF: {destino}\n"
                    self.atualizar_usuario()

                    destino_ref = self.usuarios_ref.child(destino)
                    usuario_destino = destino_ref.get()
                    if usuario_destino:
                        novo_saldo_destino = usuario_destino['Saldo'] + valor
                        destino_ref.update({'Saldo': novo_saldo_destino})
                        messagebox.showinfo("Transferência", f"Transferência de R$ {valor:.2f} realizada com sucesso para o CPF: {destino}.")
                    else:
                        messagebox.showerror("Erro", "CPF do destinatário não encontrado.")
            else:
                messagebox.showerror("Erro", "Valor de transferência inválido.")
        else:
            messagebox.showerror("Erro", "Efetue o login para realizar a transferência.")

    def atualizar_usuario(self):
        cpf = self.usuarios.get('CPF')
        usuario_ref = self.usuarios_ref.child(cpf)
        usuario_ref.update({'Saldo': self.saldo, 'chequeEspecial': self.chespecial, 'chequeI': self.chequeI})

class Interface:
    def __init__(self, root, banco):
        self.banco = banco
        self.root = root
        self.root.title("Banco TDS0025")
        self.root.geometry("500x500")

        self.imagem_fundo = PhotoImage(file="C:\\Users\\964030\\Documents\\GitHub\\banoVfinal\\logo-removebg-preview.png")
        self.label_imagem = Label(root, image=self.imagem_fundo)
        self.label_imagem.pack()

        self.cadastrar_tela = ttk.Frame(root)
        self.login_tela = ttk.Frame(root)
        self.principal_tela = ttk.Frame(root)

        self.tela_cadastro()
        self.tela_login()
        self.tela_principal()

        self.login_tela.pack(fill="both", expand=True)

    def tela_login(self):
        Label(self.login_tela, text="CPF:").pack()
        self.cpf_login = ttk.Entry(self.login_tela)
        self.cpf_login.pack()

        Label(self.login_tela, text="Senha:").pack()
        self.senha_login = ttk.Entry(self.login_tela, show="*")
        self.senha_login.pack()

        self.btn_login = ttk.Button(self.login_tela, text="Login", command=self.fazer_login)
        self.btn_login.pack()

        self.btn_ir_para_cadastro = ttk.Button(self.login_tela, text="Cadastre-se", command=self.mostrar_tela_cadastro)
        self.btn_ir_para_cadastro.pack()

    def tela_cadastro(self):
        Label(self.cadastrar_tela, text="Nome:").pack()
        self.nome_cadastro = ttk.Entry(self.cadastrar_tela)
        self.nome_cadastro.pack()

        Label(self.cadastrar_tela, text="CPF:").pack()
        self.cpf_cadastro = ttk.Entry(self.cadastrar_tela)
        self.cpf_cadastro.pack()

        Label(self.cadastrar_tela, text="Senha:").pack()
        self.senha_cadastro = ttk.Entry(self.cadastrar_tela, show="*")
        self.senha_cadastro.pack()

        Label(self.cadastrar_tela, text="Saldo Inicial:").pack()
        self.saldo_cadastro = ttk.Entry(self.cadastrar_tela)
        self.saldo_cadastro.pack()

        self.btn_cadastrar = ttk.Button(self.cadastrar_tela, text="Cadastrar", command=self.cadastrar_usuario)
        self.btn_cadastrar.pack()

        self.btn_ir_para_login = ttk.Button(self.cadastrar_tela, text="Voltar", command=self.mostrar_tela_login)
        self.btn_ir_para_login.pack()

    def tela_principal(self):
        self.btn_saldo = ttk.Button(self.principal_tela, text="Ver Saldo", command=self.mostrar_extrato)
        self.btn_saldo.pack()

        self.btn_sacar = ttk.Button(self.principal_tela, text="Sacar", command=self.sacar)
        self.btn_sacar.pack()

        self.btn_depositar = ttk.Button(self.principal_tela, text="Depositar", command=self.depositar)
        self.btn_depositar.pack()

        self.btn_transferir = ttk.Button(self.principal_tela, text="Transferir", command=self.transferir)
        self.btn_transferir.pack()

        self.btn_sair = ttk.Button(self.principal_tela, text="Sair", command=self.sair)
        self.btn_sair.pack()

    def mostrar_tela_login(self):
        self.cadastrar_tela.pack_forget()
        self.login_tela.pack(fill="both", expand=True)

    def mostrar_tela_cadastro(self):
        self.login_tela.pack_forget()
        self.cadastrar_tela.pack(fill="both", expand=True)

    def mostrar_tela_principal(self):
        self.login_tela.pack_forget()
        self.principal_tela.pack(fill="both", expand=True)

    def fazer_login(self):
        cpf = self.cpf_login.get()
        senha = self.senha_login.get()
        if self.banco.login(cpf, senha):
            self.mostrar_tela_principal()

    def cadastrar_usuario(self):
        nome = self.nome_cadastro.get()
        cpf = self.cpf_cadastro.get()
        senha = self.senha_cadastro.get()
        saldo = self.saldo_cadastro.get()

        if nome and cpf and senha and saldo:
            try:
                saldo = float(saldo)
            except ValueError:
                messagebox.showerror("Erro", "Saldo inválido.")
                return
            self.banco.cadastrar_usuario(nome, cpf, senha, saldo)
            self.mostrar_tela_login()
        else:
            messagebox.showerror("Erro", "Preencha todos os campos.")

    def mostrar_extrato(self):
        self.banco.fExtrato()
        top = tk.Toplevel()
        top.geometry("600x400")
        top.title("Extrato")

    def sacar(self):
        valor = self.obter_valor_operacao("Digite o valor do saque:")
        if valor:
            self.banco.sacar(valor)

    def depositar(self):
        valor = self.obter_valor_operacao("Digite o valor do depósito:")
        if valor:
            self.banco.depositar(valor)

    def transferir(self):
        destino = self.obter_cpf_destino("Digite o CPF do destinatário:")
        valor = self.obter_valor_operacao("Digite o valor da transferência:")
        if destino and valor:
            self.banco.transferir(destino, valor)

    def sair(self):
        self.banco.sair()
        self.root.quit()

    def obter_valor_operacao(self, mensagem):
        valor_str = tk.simpledialog.askstring("Valor", mensagem)
        try:
            valor = float(valor_str)
            return valor
        except (ValueError, TypeError):
            messagebox.showerror("Erro", "Valor inválido.")
            return None

    def obter_cpf_destino(self, mensagem):
        return tk.simpledialog.askstring("CPF", mensagem)

if __name__ == "__main__":
    banco = Banco()
    root = tk.Tk()
    root.configure(background="#001E3F")
    app = Interface(root, banco)
    root.mainloop()
