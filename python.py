import discord, random, asyncio, sqlite3, hashlib, time
from discord.ext import commands, tasks
from discord import app_commands

T="MTQ0MTczNjUyOTQ4MjQ4NTgzMQ.GBFu2R.64cVtc4QyqQI15F_Z0jdoXjXCj2iCmcujvo21U"
G=None
D="1339188304066646046"
DP="Tmdoomsday"
DB='casino_v4.db'
C_N="$"
I_B=1000.00
M_L=50.00
D_I=0.04
B_D=30
# 새로운 경제 시스템 상수
MAX_STEAL_PERCENT=0.07 # 최대 습격 가능 비율 (7%)
VAULT_DAILY_TAX=0.03   # 금고 일일 수수료 (3%)
S_I=[
    {'e': '🍒', 'w': 5, 'p': 2},
    {'e': '🔔', 'w': 4, 'p': 5},
    {'e': '💰', 'w': 3, 'p': 10},
    {'e': '💎', 'w': 2, 'p': 50},
    {'e': '⭐', 'w': 1, 'p': 200},
    {'e': '🍋', 'w': 3, 'p': 1},  # 가중치 3으로 추가 하향 (확률 상향)
    {'e': '💵', 'w': 2, 'p': 1},   # 가중치 2로 추가 하향 (확률 상향)
    {'e': '🐡', 'w': 2, 'p': 20}
]
S_V=0.05
S_M=0.50
S_DL=7
ST={"INFERNO": {"n": "인페르노철강", "p": 10.00, "t": 10000},"DOOMSDAY": {"n": "팀둠스데이", "p": 25.00, "t": 5000},"RAMSIN": {"n": "램신먹튀주식회사", "p": 1.50, "t": 50000},"GRANDPA": {"n": "의찬딸피요양원", "p": 50.00, "t": 2000},"PUFFER": {"n": "상자복어독ETF", "p": 80.00, "t": 1000},"ROCKET": {"n": "개경민로켓개발연구소", "p": 120.00, "t": 500},"SURGERY": {"n": "김성진사각턱성형외과", "p": 30.00, "t": 3000},"IKSAN_ETF": {"n": "전북익산ETF", "p": 5.00, "t": 15000},"HS_VIDEO": {"n": "현성비디오", "p": 18.00, "t": 8000},"ILBUP": {"n": "일법반도체", "p": 45.00, "t": 2500},"HOSU": {"n": "호남의왕보컬학원", "p": 15.00, "t": 10000},"DEMENTIA": {"n": "치매광전자", "p": 70.00, "t": 1500},"DRIVE": {"n": "아이스대리운전", "p": 22.00, "t": 7000}}

def h(p):return hashlib.sha256(p.encode()).hexdigest()
def fc(a):return f"{C_N}{a:,.2f}"
def s_db():
    c=sqlite3.connect(DB);cur=c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS balances (user_id TEXT PRIMARY KEY,balance REAL DEFAULT 0.0,vault_balance REAL DEFAULT 0.0,vault_password TEXT DEFAULT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS loans (user_id TEXT PRIMARY KEY,loan_amount REAL DEFAULT 0.0,last_interest_date REAL DEFAULT 0.0,is_banned INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS stocks (ticker TEXT PRIMARY KEY,price REAL DEFAULT 0.0,delist_counter INTEGER DEFAULT 0,daily_change_percent REAL DEFAULT 0.0)")
    cur.execute("CREATE TABLE IF NOT EXISTS portfolio (user_id TEXT,ticker TEXT,shares INTEGER DEFAULT 0,PRIMARY KEY (user_id, ticker))")
    c.commit()
    for t,d in ST.items():
        cur.execute("SELECT ticker FROM stocks WHERE ticker = ?",(t,))
        if cur.fetchone() is None:cur.execute("INSERT INTO stocks (ticker, price) VALUES (?, ?)",(t,d['p']))
    c.commit();c.close()

def g_b(u):
    c=sqlite3.connect(DB);cur=c.cursor();u=str(u)
    cur.execute("SELECT balance FROM balances WHERE user_id = ?",(u,));r=cur.fetchone()
    if r is None:
        cur.execute("INSERT INTO balances (user_id, balance) VALUES (?, ?)",(u,I_B));c.commit();c.close();return I_B
    c.close();return r[0]

def s_b(u,a):
    c=sqlite3.connect(DB);cur=c.cursor();u=str(u)
    cur.execute("INSERT OR REPLACE INTO balances (user_id, balance, vault_balance, vault_password) SELECT ?, ?, vault_balance, vault_password FROM balances WHERE user_id = ? ON CONFLICT(user_id) DO UPDATE SET balance=?",(u,a,u,a))
    c.commit();c.close()

def g_v(u):
    c=sqlite3.connect(DB);cur=c.cursor();u=str(u)
    cur.execute("SELECT vault_balance, vault_password FROM balances WHERE user_id = ?",(u,));r=cur.fetchone()
    if r is None:g_b(u);return 0.0,None
    c.close();return r[0],r[1]

def s_v(u,v=None,p=None):
    c=sqlite3.connect(DB);cur=c.cursor();u=str(u)
    if v is not None:cur.execute("UPDATE balances SET vault_balance = ? WHERE user_id = ?",(v,u))
    if p is not None:cur.execute("UPDATE balances SET vault_password = ? WHERE user_id = ?",(p,u))
    c.commit();c.close()

def g_sp(t):
    c=sqlite3.connect(DB);cur=c.cursor()
    cur.execute("SELECT price FROM stocks WHERE ticker = ?",(t,));r=cur.fetchone()
    c.close();return r[0] if r else None

def g_us(u,t):
    c=sqlite3.connect(DB);cur=c.cursor()
    cur.execute("SELECT shares FROM portfolio WHERE user_id = ? AND ticker = ?",(str(u),t));r=cur.fetchone()
    c.close();return r[0] if r else 0

def u_us(u,t,s):
    c=sqlite3.connect(DB);cur=c.cursor();u=str(u)
    cs=g_us(u,t);ns=cs+s
    if ns<0:c.close();return False
    if ns==0:cur.execute("DELETE FROM portfolio WHERE user_id = ? AND ticker = ?",(u,t))
    else:cur.execute("INSERT OR REPLACE INTO portfolio (user_id, ticker, shares) VALUES (?, ?, ?)",(u,t,ns))
    c.commit();c.close();return True

def g_all_s():
    c=sqlite3.connect(DB);cur=c.cursor()
    cur.execute("SELECT ticker, price, delist_counter, daily_change_percent FROM stocks");r=cur.fetchall()
    c.close();return r

def g_all_v_tax_users():
    c=sqlite3.connect(DB);cur=c.cursor()
    # 금고 잔액이 0보다 큰 사용자들의 ID와 잔액을 가져옵니다.
    cur.execute("SELECT user_id, vault_balance FROM balances WHERE vault_balance > 0");r=cur.fetchall()
    c.close();return r

def g_l(u):
    c=sqlite3.connect(DB);cur=c.cursor();u=str(u)
    cur.execute("SELECT loan_amount, last_interest_date, is_banned FROM loans WHERE user_id = ?",(u,));r=cur.fetchone()
    c.close()
    # 사용자의 대출 기록이 없으면 (r이 None이면) 기본값 반환
    if r is None:
        return 0.0, 0.0, 0
    return r[0], r[1], r[2] # 데이터가 있으면 튜플의 요소 반환

def u_l(u,a,l,i):
    c=sqlite3.connect(DB);cur=c.cursor();u=str(u)
    cur.execute("INSERT OR REPLACE INTO loans (user_id, loan_amount, last_interest_date, is_banned) VALUES (?, ?, ?, ?)",(u,a,l,i))
    c.commit();c.close()

def g_al():
    c=sqlite3.connect(DB);cur=c.cursor()
    cur.execute("SELECT user_id, loan_amount, last_interest_date, is_banned FROM loans WHERE loan_amount > 0 OR is_banned = 1");r=cur.fetchall()
    c.close();return r

def g_p(u):
    c=sqlite3.connect(DB);cur=c.cursor()
    cur.execute("SELECT ticker, shares FROM portfolio WHERE user_id = ?",(str(u),));r=cur.fetchall()
    c.close();return r

def g_ta(u):
    b=g_b(u);v,_=g_v(u);l,_,_=g_l(u);pv=0.0
    for t,s in g_p(u):
        p=g_sp(t)
        if p:pv+=p*s
    return b+v+pv-l

def g_tb(l):
    c=sqlite3.connect(DB);cur=c.cursor();cur.execute("SELECT user_id FROM balances");uids=[r[0] for r in cur.fetchall()];al=[]
    for u in uids:al.append((u,g_ta(int(u))))
    al.sort(key=lambda item:item[1],reverse=True);c.close();return al[:l]

# A, B, C 선택 게임을 위한 View 클래스
class ChoiceView(discord.ui.View):
    def __init__(self, original_user_id, bet_amount, timeout=180):
        super().__init__(timeout=timeout)
        self.original_user_id = original_user_id
        self.bet_amount = bet_amount
        self.chosen = False
        self.result = random.choice(['A', 'B', 'C'])

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message("❌ 이 게임은 당신의 게임이 아닙니다.", ephemeral=True)
            return False
        if self.chosen:
            await interaction.response.send_message("❌ 이미 선택을 완료했습니다.", ephemeral=True)
            return False
        return True

    # interaction 인수를 추가했습니다. (이전 오류 수정 반영)
    def update_embed(self, interaction: discord.Interaction, embed, choice, win):
        title = "🥳 승리!" if win else "😭 패배..."
        color = discord.Color.green() if win else discord.Color.red()
        
        # 잔액 계산 및 DB 업데이트
        user_id = self.original_user_id
        winnings = self.bet_amount * 3 if win else -self.bet_amount
        bal = g_b(user_id)
        nb = bal + winnings
        s_b(user_id, nb)
        
        # interaction.user.display_name을 사용하여 사용자 이름을 가져옵니다.
        embed.title = f"🎲 1/3 도박 ({interaction.user.display_name}) {title}"
        embed.color = color
        embed.clear_fields()
        embed.add_field(name="베팅 금액", value=fc(self.bet_amount), inline=True)
        embed.add_field(name="선택", value=f"**{choice}**", inline=True)
        embed.add_field(name="결과", value=f"**{self.result}**", inline=True)
        embed.add_field(name="손익", value=fc(winnings), inline=False)
        embed.add_field(name="남은 잔액", value=fc(nb), inline=False)
        return embed

    def disable_all(self):
        for item in self.children:
            item.disabled = True

    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        self.chosen = True
        win = (choice == self.result)
        
        self.disable_all()
        
        # interaction을 인수로 전달
        updated_embed = self.update_embed(interaction, interaction.message.embeds[0], choice, win)
        
        await interaction.response.edit_message(embed=updated_embed, view=self)

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def choice_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, 'A')

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def choice_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, 'B')

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def choice_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, 'C')

class B(commands.Bot):
    def __init__(self):super().__init__(command_prefix=commands.when_mentioned_or("!"),intents=discord.Intents.all())
    async def setup_hook(self):
        s_db();await self.add_cog(C(self))
        try:
            if G:
                g=discord.Object(id=G);self.tree.copy_global_to(guild=g);s=await self.tree.sync(guild=g)
                print(f"✅ 특정 길드 ({G}) 동기화. ({len(s)}개)")
            else:s=await self.tree.sync();print(f"✅ 전역 동기화. ({len(s)}개)")
        except Exception as e:print(f"⚠️ 동기화 오류: {e}")
    async def on_ready(self):
        print(f"✅ 봇 ({self.user}) 준비 완료! DB: {DB}")
        if self.get_cog('C'):self.get_cog('C').d_i.start();self.get_cog('C').d_s.start()
    def is_developer(self,u):return str(u)==D

class C(commands.Cog):
    cg=app_commands.Group(name="카지노",description="슬롯 게임 및 카지노 명령어")
    vg=app_commands.Group(name="금고",description="개인 금고 및 달러 입/출금 명령어")
    sg=app_commands.Group(name="주식",description="가상 주식 시장 명령어")
    dg=app_commands.Group(name="개발자",description="개발자 전용 관리 명령어")
    def __init__(self,b:B):
        self.bot=b
        self.raid_cooldowns = {} # 습격 쿨다운 관리용 딕셔너리

    def g_r(self):
        p=[i['e'] for i in S_I for _ in range(i['w'])];return random.choice(p)

    def c_w(self,r,b):
        # r: 9개의 결과 심볼 리스트 (3x3)
        lines = [
            r[0:3], # Line 1
            r[3:6], # Line 2
            r[6:9]  # Line 3
        ]
        
        winnings_total = -b
        message = "😔 아쉽네요! 다음 기회에..."
        jackpot_lines = []
        
        # 가로 3줄 잭팟 확인
        for line_index, line in enumerate(lines):
            if line[0] == line[1] and line[1] == line[2]:
                symbol = line[0]
                for i in S_I:
                    if i['e'] == symbol:
                        # 3x3 잭팟 시 10배 지급 (multiplier * 10)
                        multiplier = i['p'] * 10 
                        winnings_total += b * multiplier
                        jackpot_lines.append(f"🎉 Line {line_index+1}: {symbol}{symbol}{symbol} **슈퍼 잭팟!** {multiplier}배 획득!")
                        break

        # 잭팟이 터졌다면 해당 메시지들을 출력
        if jackpot_lines:
            message = "\n".join(jackpot_lines)
            final_w = sum(b * (i['p'] * 10) for line in lines if line[0] == line[1] and line[1] == line[2] for i in S_I if i['e'] == line[0]) - b
            return (final_w, message)

        # 잭팟이 없으면 기본 패배 메시지
        return (winnings_total, message)
    
    def g_ss(self, c):
        if c>=10.0:return ("개떡상","🚀",discord.Color.blue())
        if c>=5.0:return ("떡상","📈",discord.Color.green())
        if c>=2.0:return ("주목","✨",discord.Color.brand_red())
        if c<=-10.0:return ("개떡락","🔥🔥",discord.Color.red())
        if c<=-5.0:return ("떡락","📉",discord.Color.orange())
        if c<=-2.0:return ("관심","🔻",discord.Color.yellow())
        return ("안정적","🟢",discord.Color.light_grey())

    def g_ss_name(self, c):
        if c>=10.0:return "개떡상"
        if c>=5.0:return "떡상"
        if c>=2.0:return "주목"
        if c<=-10.0:return "개떡락"
        if c<=-5.0:return "떡락"
        if c<=-2.0:return "관심"
        return "안정적"

    @tasks.loop(hours=24)
    async def d_i(self):
        t=time.time();ls=g_al()
        
        # 1. 대출 이자 및 밴 처리
        for u,a,l,i in ls:
            uid=int(u);usr=self.bot.get_user(uid)
            if i:continue
            dp=(t-l)//(24*3600);
            if dp<1:continue
            for _ in range(int(dp)):a+=a*D_I
            if t-l>B_D*24*3600 and a>M_L:
                s_b(uid,max(0.0,g_b(uid)-a));u_l(uid,0.0,t,1)
                if usr:
                    try:await usr.send(f"⚠️ **경고: 대출금 미상환!**\n30일 이상 대출금 **{fc(a)}**을 상환하지 않아, 잔액에서 차감되었으며, **대출 기능이 정지**되었습니다.")
                    except:pass
                continue
            u_l(uid,a,t,i)
            if usr and a>0.0 and dp>=1:
                try:
                    await usr.send(f"🔔 **대출 이자 부과 알림**\n대출 원금에 {int(dp*D_I*100)}%의 이자가 추가되어, 현재 상환할 금액은 **{fc(a)}**입니다.")
                except:
                    pass

        # 2. 금고 일일 수수료 (Vault Tax) 부과
        vault_users = g_all_v_tax_users()
        for u_str, v_bal in vault_users:
            uid = int(u_str)
            usr = self.bot.get_user(uid)
            tax_amount = round(v_bal * VAULT_DAILY_TAX, 2)
            new_v_bal = round(v_bal - tax_amount, 2)
            s_v(uid, new_v_bal) # 금고 잔액 업데이트
            
            if usr:
                try:
                    await usr.send(f"💸 **금고 수수료 알림**\n불우아동지원비로 금고 잔액의 3%인 **{fc(tax_amount)}**가 차감되었습니다. 남은 금고 잔액: {fc(new_v_bal)}")
                except:
                    pass

    @d_i.before_loop
    async def b_d_i(self):await self.bot.wait_until_ready()

    @tasks.loop(hours=1) # 2시간 -> 1시간으로 변경
    async def d_s(self):
        c=sqlite3.connect(DB);cur=c.cursor();all_s=g_al()
        for t,cp,dlc,dc in g_all_s():
            d=ST.get(t)
            if not d:continue
            ts=d['t'];os=self.g_ts(t);bc=random.uniform(-S_V,S_V);ir=os/ts if ts>0 else 0;sf=1.0-(ir*0.5);fc=bc*sf
            np=cp*(1.0+fc);np=round(max(S_M*0.9,np),2);ndlc=dlc
            if np<=S_M:ndlc+=1
            else:ndlc=0
            if ndlc>=S_DL:
                fp=0.01;cur.execute("SELECT user_id, shares FROM portfolio WHERE ticker = ?",(t,));pr=cur.fetchall()
                for uid_str,sh in pr:
                    uid=int(uid_str);p=sh*fp;s_b(uid,g_b(uid)+p);usr=self.bot.get_user(uid)
                    if usr:
                         try:await usr.send(f"⚠️ **상장 폐지 알림: {d['n']} ({t})**\n주가가 장기간 **{fc(S_M)}** 이하로 유지되어 상장 폐지되었습니다. {sh}주에 대해 **{fc(p)}**가 지급되었습니다.")
                         except:pass
                cur.execute("DELETE FROM portfolio WHERE ticker = ?",(t,));cur.execute("DELETE FROM stocks WHERE ticker = ?",(t,))
            else:
                pc_s=fc*100
                cur.execute("INSERT OR REPLACE INTO stocks (ticker, price, delist_counter, daily_change_percent) VALUES (?, ?, ?, ?)",(t,np,ndlc,pc_s))
        c.commit();c.close()

    @d_s.before_loop
    async def b_d_s(self):await self.bot.wait_until_ready()

    def g_ts(self,t):
        c=sqlite3.connect(DB);cur=c.cursor()
        cur.execute("SELECT SUM(shares) FROM portfolio WHERE ticker = ?",(t,));r=cur.fetchone()
        c.close();return r[0] if r and r[0] else 0

    @app_commands.command(name="잔액", description="현재 지갑과 금고의 잔액을 확인합니다.")
    async def b(self,i:discord.Interaction):
        # 이 명령어는 사적인 정보이므로 ephemeral=True 유지
        await i.response.defer(ephemeral=True) 
        u=i.user.id
        b=g_b(u);v,_=g_v(u);l,_,_=g_l(u);pv=0.0
        for t,s in g_p(u):
            p=g_sp(t)
            if p:pv+=p*s
        ta=g_ta(u);e=discord.Embed(title="💰 자산 현황",color=discord.Color.gold())
        e.add_field(name="지갑 잔액 (Wallet)",value=fc(b),inline=False)
        e.add_field(name="금고 잔액 (Vault)",value=fc(v),inline=False)
        e.add_field(name="주식 자산 (Portfolio)",value=fc(pv),inline=False)
        e.add_field(name="상환할 대출금 (Loan)",value=fc(l),inline=False)
        e.add_field(name="총 순자산 (Net Total)",value=fc(ta),inline=False)
        e.set_thumbnail(url=i.user.avatar.url if i.user.avatar else i.user.default_avatar.url)
        await i.followup.send(embed=e) 

    @app_commands.command(name="순위표", description="총 순자산 순위표를 확인합니다.")
    async def ld(self,i:discord.Interaction):
        await i.response.defer();tp=g_tb(10)
        if not tp:await i.followup.send("아직 플레이한 사람이 없어 순위표가 비어있습니다!")
        else:
            d=""
            for j,(uid_str,a) in enumerate(tp):
                u=self.bot.get_user(int(uid_str));un=u.display_name if u else f"알 수 없는 사용자 ({uid_str[:5]}...)"
                d+=f"**{j+1}. {un}**: {fc(a)}\n"
            e=discord.Embed(title="🏆 총 순자산 순위표 🏆",description=d,color=discord.Color.orange())
            e.set_footer(text="총 순자산 = 지갑 + 금고 + 주식 평가액 - 대출금")
            await i.followup.send(embed=e)
        
    @dg.command(name="재시작", description="개발자 전용: 봇을 종료하여 재시작을 준비합니다.")
    async def r_b(self,i:discord.Interaction):
        if not self.bot.is_developer(i.user.id):await i.response.send_message("❌ 이 명령어는 개발자 전용입니다.",ephemeral=True);return
        await i.response.send_message("⚙️ 봇을 종료하고 재시작을 준비합니다...",ephemeral=False);await self.bot.close()
    
    @dg.command(name="돈지급", description="개발자 전용: 특정 사용자에게 달러를 지급합니다.")
    @app_commands.describe(t_user="지급할 사용자", a="지급할 금액")
    async def grant_money(self, i: discord.Interaction, t_user: discord.User, a: float):
        if not self.bot.is_developer(i.user.id):
            await i.response.send_message("❌ 이 명령어는 개발자 전용입니다.", ephemeral=True); return
        if a <= 0:
            await i.response.send_message("❌ 지급 금액은 0보다 커야 합니다.", ephemeral=True); return
        
        cb = g_b(t_user.id)
        s_b(t_user.id, cb + a)
        await i.response.send_message(f"✅ **{t_user.display_name}** 님에게 **{fc(a)}**를 지급했습니다.\n현재 잔액: {fc(cb + a)}", ephemeral=True)

    @dg.command(name="파산복구", description="개발자 전용: 특정 사용자의 잔액을 초기 금액으로 복구합니다.")
    @app_commands.describe(t_user="복구할 사용자")
    async def reset_bankruptcy(self, i: discord.Interaction, t_user: discord.User):
        if not self.bot.is_developer(i.user.id):
            await i.response.send_message("❌ 이 명령어는 개발자 전용입니다.", ephemeral=True); return
        
        # 지갑 잔액을 초기 금액으로 복구
        s_b(t_user.id, I_B)
        
        # 대출 기록 초기화 (대출금 0, 밴 해제)
        u_l(t_user.id, 0.0, 0.0, 0)
        
        await i.response.send_message(f"✅ **{t_user.display_name}** 님의 지갑 잔액을 초기 금액인 **{fc(I_B)}**로 복구하고 대출 기록을 초기화했습니다.", ephemeral=True)

    @cg.command(name="슬롯", description="슬롯 머신에 베팅합니다.")
    @app_commands.describe(b="베팅할 금액")
    async def s(self,i:discord.Interaction,b:float):
        u=i.user.id
        if b<=0:await i.response.send_message("❌ 베팅 금액은 0보다 커야 합니다.",ephemeral=True);return
        bal=g_b(u)
        if bal<b:await i.response.send_message(f"❌ 잔액 부족! 현재 잔액: {fc(bal)}",ephemeral=True);return
        await i.response.defer() # 모두에게 보이기 (ephemeral=False)
        
        # 3x3 포맷 초기화 (구분선 11글자로 수정)
        result_display = "```\n? | ? | ?\n-----------\n? | ? | ?\n-----------\n? | ? | ?\n```"
        be=discord.Embed(title=f"🎰 슬롯 머신 ({i.user.display_name})",description=f"**베팅 금액:** {fc(b)}\n\n**슬롯이 돌아갑니다!**",color=discord.Color.light_grey())
        be.add_field(name="결과",value=result_display,inline=False) 
        m=await i.followup.send(embed=be)
        
        ae=[_['e'] for _ in S_I]
        # 애니메이션 속도 0.02초로 빠르게, 롤링 횟수 6회로 증가
        for _ in range(6): 
            rr=[random.choice(ae) for _ in range(9)] # 9개 결과 생성
            # 애니메이션 구분선 수정
            ts=f"{rr[0]} | {rr[1]} | {rr[2]}\n-----------\n{rr[3]} | {rr[4]} | {rr[5]}\n-----------\n{rr[6]} | {rr[7]} | {rr[8]}"
            be.colour=discord.Color.random()
            be.set_field_at(0,name="결과",value=f"```\n{ts}\n```",inline=False)
            await m.edit(embed=be);await asyncio.sleep(0.02) 

        r=[self.g_r() for _ in range(9)]
        # 최종 결과 구분선 수정
        rs=f"{r[0]} | {r[1]} | {r[2]}\n-----------\n{r[3]} | {r[4]} | {r[5]}\n-----------\n{r[6]} | {r[7]} | {r[8]}"
        w,rm=self.c_w(r,b);nb=bal+w;s_b(u,nb)

        fe=discord.Embed(title=f"🎰 슬롯 머신 ({i.user.display_name})",description=f"**베팅 금액:** {fc(b)}",color=discord.Color.red() if w<0 else discord.Color.green())
        fe.add_field(name="최종 결과",value=f"```\n{rs}\n```",inline=False)
        fe.add_field(name="결과 메시지",value=rm,inline=False)
        fe.add_field(name="손익",value=f"{fc(w)}",inline=True)
        fe.add_field(name="잔액",value=fc(nb),inline=True)
        await m.edit(embed=fe)

    @cg.command(name="삼분의일도박", description="3개의 버튼 중 하나를 골라 3배 금액을 노리는 게임입니다. (1/3 확률)") # 이름 및 설명 수정
    @app_commands.describe(b="베팅할 금액")
    async def choice_game(self, i: discord.Interaction, b: float):
        u = i.user.id
        if b <= 0:await i.response.send_message("❌ 베팅 금액은 0보다 커야 합니다.", ephemeral=True);return
        bal = g_b(u)
        if bal < b:await i.response.send_message(f"❌ 잔액 부족! 현재 잔액: {fc(bal)}", ephemeral=True);return
        
        # 베팅 금액을 차감하고 시작
        s_b(u, bal - b)

        e = discord.Embed(title=f"🎲 1/3 도박 ({i.user.display_name})", color=discord.Color.light_grey())
        e.add_field(name="베팅 금액", value=fc(b), inline=False)
        e.add_field(name="진행", value="A, B, C 중 하나를 선택하세요!", inline=False)

        view = ChoiceView(i.user.id, b)
        await i.response.send_message(embed=e, view=view)

    # -------------------------------------------------------------
    # 기본 도박 명령어 추가
    # -------------------------------------------------------------
    @app_commands.command(name="기본도박", description="42.9% 2배, 7% 10배, 0.1% 50배를 노리는 기본 도박입니다.")
    @app_commands.describe(b="베팅할 금액")
    async def basic_gamble(self, i: discord.Interaction, b: float):
        u = i.user.id
        
        if b <= 0:
            await i.response.send_message("❌ 베팅 금액은 0보다 커야 합니다.", ephemeral=True); return
        bal = g_b(u)
        if bal < b:
            await i.response.send_message(f"❌ 잔액 부족! 현재 잔액: {fc(bal)}", ephemeral=True); return

        # 1. 확률 결정
        r = random.random() # 0.0부터 1.0 미만의 실수
        multiplier = 0 # 0이면 잃는 것 (베팅 금액 - 베팅 금액 = 0)
        win_chance = False
        
        # 0.1% 확률: 50배
        if r < 0.001: 
            multiplier = 50 
            win_chance = True
            result_msg = "💎 대박! 50배 당첨!"
            color = discord.Color.gold()
        # 7.0% 확률: 10배 (0.1% ~ 7.1%)
        elif r < 0.071:
            multiplier = 10 
            win_chance = True
            result_msg = "💰 10배 당첨!"
            color = discord.Color.orange()
        # 42.9% 확률: 2배 (7.1% ~ 50.0%)
        elif r < 0.500:
            multiplier = 2
            win_chance = True
            result_msg = "📈 2배 당첨!"
            color = discord.Color.green()
        # 50.0% 확률: 패배 (50.0% ~ 100.0%)
        else:
            multiplier = 0
            win_chance = False
            result_msg = "😭 아쉽네요. 다음 기회에..."
            color = discord.Color.red()

        # 2. 결과 계산 및 DB 반영
        if win_chance:
            # 베팅 금액이 1배, 당첨금은 (multiplier - 1)배의 이득이 되어 총 multiplier 배를 돌려받습니다.
            winnings = b * multiplier 
            net_profit = winnings - b
        else:
            # 베팅 금액 전액 손실
            winnings = 0
            net_profit = -b
            
        nb = bal + net_profit
        s_b(u, nb) # 잔액 업데이트

        # 3. 임베드 출력 (ephemeral=False, 모두에게 보이기)
        e = discord.Embed(
            title=f"🎰 기본 도박 ({i.user.display_name})",
            description=result_msg,
            color=color
        )
        e.add_field(name="베팅 금액", value=fc(b), inline=True)
        e.add_field(name="결과 배율", value=f"**{multiplier}배**", inline=True)
        e.add_field(name="손익", value=fc(net_profit), inline=False)
        e.add_field(name="남은 잔액", value=fc(nb), inline=False)
        
        await i.response.send_message(embed=e)
        
    @cg.command(name="은행털기", description="다른 사용자의 지갑을 습격하여 달러를 훔치려 시도합니다 (6% 확률, 상대 오프라인 시).")
    @app_commands.describe(t_user="습격할 사용자")
    async def raid(self, i: discord.Interaction, t_user: discord.User):
        u = i.user.id
        tu = t_user.id
        
        # 1. 쿨다운 체크 (5분 = 300초)
        if u in self.raid_cooldowns and time.time() - self.raid_cooldowns[u] < 300:
            remaining = int(300 - (time.time() - self.raid_cooldowns[u]))
            await i.response.send_message(f"❌ 습격 쿨다운 중입니다. {remaining // 60}분 {remaining % 60}초 후에 다시 시도하세요.", ephemeral=True)
            return

        if u == tu:
            await i.response.send_message("❌ 자기 자신은 습격할 수 없습니다.", ephemeral=True)
            return

        # 2. 오프라인 상태 체크
        if t_user.status != discord.Status.offline:
            await i.response.send_message(f"❌ {t_user.display_name} 님은 현재 온라인 상태입니다. 상대가 **오프라인**일 때만 습격할 수 있습니다.", ephemeral=True)
            return
            
        t_bal = g_b(tu) # 피해자의 지갑 잔액
        r_bal = g_b(u)  # 습격자의 지갑 잔액

        if t_bal <= 0:
            await i.response.send_message(f"❌ {t_user.display_name} 님의 지갑이 비어있어 훔칠 돈이 없습니다.", ephemeral=True)
            return
            
        # 습격 시작, 쿨다운 적용
        self.raid_cooldowns[u] = time.time()
        
        # 3. 습격 성공 로직 (6% 확률)
        if random.random() < 0.06: # 0.15 -> 0.06 (6%)
            steal_percent = random.uniform(0.01, MAX_STEAL_PERCENT) # 1% to 7%
            steal_amount = round(t_bal * steal_percent, 2)
            
            # 피해자가 돈을 잃고, 습격자가 돈을 얻음
            s_b(tu, t_bal - steal_amount)
            s_b(u, r_bal + steal_amount)
            
            # ephemeral=False로 변경하여 모두에게 보이게 함
            await i.response.send_message(f"🚨 {i.user.display_name} 님이 {t_user.display_name} 님을 습격하여 **{fc(steal_amount)}**를 훔쳤습니다! (비율: {steal_percent*100:.2f}%)") 
            
            # 피해자에게 DM 알림
            try:
                await t_user.send(f"🚨 **경고: 지갑 습격 감지!**\n{i.user.display_name} 님이 귀하의 지갑에서 **{fc(steal_amount)}**를 훔쳐갔습니다. (지갑 잔액은 위험합니다. `/금고 입금`으로 보호하세요.)")
            except:
                pass
        else:
            # 습격 실패 로직
            loss = 50.00
            s_b(u, r_bal - loss)
            # ephemeral=False로 변경하여 모두에게 보이게 함
            await i.response.send_message(f"💸 {i.user.display_name} 님의 **습격 실패!** 경비원에게 붙잡혀서 수수료 **{fc(loss)}**를 지불하고 도망쳤습니다.") 

    @vg.command(name="설정", description="금고 비밀번호를 설정합니다.")
    @app_commands.describe(p="금고에 사용할 비밀번호 (숫자, 문자 가능)")
    async def vs_p(self,i:discord.Interaction,p:str):
        _,ch=g_v(i.user.id)
        if ch:await i.response.send_message("❌ 이미 금고 비밀번호가 설정되어 있습니다. 변경하려면 `/금고 변경` 명령어를 사용하세요.",ephemeral=True);return
        s_v(i.user.id, p=h(p));await i.response.send_message("✅ 금고 비밀번호가 성공적으로 설정되었습니다! 이제 안전하게 달러를 보관할 수 있습니다.",ephemeral=True)

    @vg.command(name="변경", description="금고 비밀번호를 변경합니다.")
    @app_commands.describe(cp="현재 사용 중인 비밀번호", np="새로 사용할 비밀번호")
    async def vc_p(self,i:discord.Interaction,cp:str,np:str):
        _,ch=g_v(i.user.id)
        if not ch:await i.response.send_message("❌ 설정된 금고 비밀번호가 없습니다. `/금고 설정`으로 먼저 설정하세요.",ephemeral=True);return
        if ch!=h(cp):await i.response.send_message("❌ 현재 비밀번호가 일치하지 않습니다.",ephemeral=True);return
        s_v(i.user.id, p=h(np));await i.response.send_message("✅ 금고 비밀번호가 성공적으로 변경되었습니다.",ephemeral=True)

    @vg.command(name="입금", description="지갑의 달러를 금고에 보관합니다.")
    @app_commands.describe(a="금고에 입금할 금액 ('all' 입력 가능)") 
    async def vd(self,i:discord.Interaction,a:str):
        # 금고 관련 명령어는 사적인 정보이므로 ephemeral=True 유지
        u=i.user.id;b=g_b(u);v,_=g_v(u);da=0.0
        if a.lower()=='all':da=b
        else:
            try:da=float(a)
            except ValueError:await i.response.send_message("❌ 금액은 숫자이거나 'all'이어야 합니다.",ephemeral=True);return
        if da<=0:await i.response.send_message("❌ 입금 금액은 0보다 커야 합니다.",ephemeral=True);return
        if b<da:await i.response.send_message(f"❌ 지갑 잔액 부족! 현재 잔액: {fc(b)}",ephemeral=True);return
        s_b(u,b-da);s_v(u,v+da)
        await i.response.send_message(f"✅ **{fc(da)}**를 금고에 입금했습니다.\n**금고 잔액:** {fc(v+da)} | **지갑 잔액:** {fc(b-da)}",ephemeral=True)

    @vg.command(name="출금", description="금고의 달러를 지갑으로 출금합니다.")
    @app_commands.describe(a="금고에서 출금할 금액 ('all' 입력 가능)", p="설정한 금고 비밀번호") 
    async def vw(self,i:discord.Interaction,a:str,p:str):
        # 금고 관련 명령어는 사적인 정보이므로 ephemeral=True 유지
        u=i.user.id;b=g_b(u);v,ph=g_v(u)
        if not ph:await i.response.send_message("❌ 금고 비밀번호가 설정되어 있지 않습니다.",ephemeral=True);return
        if ph!=h(p):await i.response.send_message("❌ 비밀번호가 일치하지 않습니다.",ephemeral=True);return
        wa=0.0
        if a.lower()=='all':wa=v
        else:
            try:wa=float(a)
            except ValueError:await i.response.send_message("❌ 금액은 숫자이거나 'all'이어야 합니다.",ephemeral=True);return
        if wa<=0:await i.response.send_message("❌ 출금 금액은 0보다 커야 합니다.",ephemeral=True);return
        if v<wa:await i.response.send_message(f"❌ 금고 잔액 부족! 현재 금고 잔액: {fc(v)}",ephemeral=True);return
        s_b(u,b+wa);s_v(u,v-wa)
        await i.response.send_message(f"✅ **{fc(wa)}**를 금고에서 출금했습니다.\n**금고 잔액:** {fc(v-wa)} | **지갑 잔액:** {fc(b+wa)}",ephemeral=True)

    @app_commands.command(name="대출", description="소액의 달러를 대출받습니다.")
    async def l(self,i:discord.Interaction):
        u=i.user.id;a,_,ib=g_l(u)
        if ib:await i.response.send_message(f"❌ 대출 기능이 정지되었습니다.",ephemeral=False);return
        if a>0:await i.response.send_message(f"❌ 이미 대출받은 금액 **{fc(a)}**이 있습니다. 상환 후 다시 시도하세요.",ephemeral=False);return
        na=M_L;cb=g_b(u);s_b(u,cb+na);u_l(u,na,time.time(),0)
        # ephemeral=False로 변경하여 모두에게 보이게 함
        await i.response.send_message(f"🎉 **{i.user.display_name}** 님이 **{fc(na)}**을 대출받았습니다! 💸\n**주의:** 일일 {int(D_I*100)}%의 이자가 부과됩니다. 상환할 금액: {fc(na)}") 

    @app_commands.command(name="상환", description="대출금을 상환합니다.")
    async def r(self,i:discord.Interaction):
        u=i.user.id;a,_,ib=g_l(u);cb=g_b(u)
        if a<=0:
            m="❌ 상환할 대출 금액이 없습니다."
            if ib:m="⚠️ 현재 대출 기능이 정지된 상태이지만, 상환할 금액은 없습니다."
            await i.response.send_message(m,ephemeral=False);return
        if cb<a:await i.response.send_message(f"❌ 잔액 부족! 상환해야 할 금액: **{fc(a)}**",ephemeral=False);return
        s_b(u,cb-a);u_l(u,0.0,0.0,0)
        # ephemeral=False로 변경하여 모두에게 보이게 함
        await i.response.send_message(f"✅ **{i.user.display_name}** 님이 대출금 **{fc(a)}**을 전액 상환했습니다! 🥳\n**현재 잔액:** {fc(cb-a)}")

    @app_commands.command(name="송금", description="다른 사용자에게 달러를 보냅니다.")
    @app_commands.describe(t_user="달러를 받을 사용자", a="송금할 금액")
    async def transfer(self, i: discord.Interaction, t_user: discord.User, a: float):
        u = i.user.id
        tu = t_user.id
        
        if u == tu:await i.response.send_message("❌ 자기 자신에게 송금할 수 없습니다.", ephemeral=True);return
        if a <= 0:await i.response.send_message("❌ 송금 금액은 0보다 커야 합니다.", ephemeral=True);return

        bal = g_b(u)
        if bal < a:await i.response.send_message(f"❌ 잔액 부족! 현재 잔액: {fc(bal)}", ephemeral=True);return

        # 송금인 잔액 차감
        s_b(u, bal - a)
        # 수신인 잔액 증가
        t_bal = g_b(tu)
        s_b(tu, t_bal + a)

        await i.response.defer() # ephemeral=False (모두에게 보이기)
        
        # 송금 정보 임베드
        e = discord.Embed(title="💸 달러 송금 완료", color=discord.Color.blue())
        e.add_field(name="보낸 사람", value=i.user.display_name, inline=True)
        e.add_field(name="받는 사람", value=t_user.display_name, inline=True)
        e.add_field(name="송금 금액", value=fc(a), inline=False)
        e.add_field(name="남은 잔액 (송금인)", value=fc(bal - a), inline=False)
        
        await i.followup.send(embed=e)
        
        # 수신자에게 DM 알림
        try:
            await t_user.send(f"🔔 **{i.user.display_name}** 님으로부터 **{fc(a)}**를 송금받았습니다.")
        except:
            pass

    @sg.command(name="목록", description="현재 상장된 모든 주식의 정보를 확인합니다.")
    async def sl(self,i:discord.Interaction):
        await i.response.defer();all_s=g_all_s()
        if not all_s:await i.followup.send("현재 상장된 주식이 없습니다.",ephemeral=False);return
        d="### 상장 주식 현황\n"
        first_color=discord.Color.blue()
        for t,p,dlc,cp in all_s:
            sn=ST.get(t,{}).get('n',t);status,emoji,color=self.g_ss(cp)
            if not first_color:first_color=color 
            dw=""
            if dlc>0:dw=f" ⚠️({dlc}/{S_DL}일 연속 최저가)"
            d+=f"{emoji} **[{status}] {sn}** ({ST[t]['t']}주): **{fc(p)}** ({cp:+.2f}%) {dw} | _{status}_\n"
        e=discord.Embed(title="📈 가상 주식 시장",description=d,color=first_color)
        e.set_footer(text=f"일일 변동률: 최대 {int(S_V*100)}% | 상장 폐지 기준: {fc(S_M)}")
        await i.followup.send(embed=e)

    @sg.command(name="매수", description="주식을 구매합니다.")
    @app_commands.describe(t="구매할 주식 이름 또는 상태 (예: 인페르노철강, 떡상)", s="구매할 주식 수량") 
    async def sb(self,i:discord.Interaction,t:str,s:int):
        await i.response.defer() # ephemeral=False (모두에게 보이기)
        u=i.user.id
        
        t_upper=t.upper()
        STATUS_NAMES = ["개떡상", "떡상", "주목", "개떡락", "떡락", "관심", "안정적"]
        
        found_t=None
        
        # 1. 주식 이름 확인 (우선 순위)
        for ticker, data in ST.items():
            if data['n'].upper() == t_upper:
                found_t=ticker
                break
                    
        # 2. 상태명 확인
        if not found_t and t_upper in [s.upper() for s in STATUS_NAMES]:
            target_status_name = t_upper
            matching_tickers = []
            
            all_s = g_all_s() 
            for ticker, price, delist_counter, daily_change_percent in all_s:
                current_status_name = self.g_ss_name(daily_change_percent).upper()
                
                if current_status_name == target_status_name:
                    matching_tickers.append(ticker)
            
            if len(matching_tickers) == 1:
                found_t = matching_tickers[0]
            elif len(matching_tickers) > 1:
                ticker_list = ", ".join([f"{ST[mt]['n']} ({mt})" for mt in matching_tickers])
                await i.followup.send(f"⚠️ **'{t}'** 상태를 가진 주식이 여러 개 있습니다 ({ticker_list}). 주식 이름으로 정확히 지정해 주세요.")
                return
            
        # 3. 티커 입력을 허용하지 않음 (이름이나 상태명이 아닌 경우 거부)
        if not found_t:
            await i.followup.send("❌ 존재하지 않는 주식 이름 또는 상태입니다. `/주식 목록`을 확인하세요.")
            return
        
        t=found_t
        
        p=g_sp(t);
        if p is None:await i.followup.send("❌ 상장 폐지된 주식입니다.");return
        if s<=0:await i.followup.send("❌ 주식 수량은 1개 이상이어야 합니다.");return
        c=p*s;cb=g_b(u)
        if cb<c:await i.followup.send(f"❌ 잔액 부족! {s}주를 구매하려면 {fc(c)}가 필요합니다. 현재 잔액: {fc(cb)}");return
        s_b(u,cb-c);u_us(u,t,s)
        # ephemeral=False로 변경하여 모두에게 보이게 함
        await i.followup.send(f"✅ **{i.user.display_name}** 님이 **{ST[t]['n']}** 주식 **{s}주**를 **{fc(c)}**에 매수했습니다. 현재 보유: {g_us(u,t)}주") 

    @sg.command(name="매도", description="주식을 판매합니다.")
    @app_commands.describe(t="판매할 주식 이름 또는 상태 (예: 인페르노철강, 떡상)", s="판매할 주식 수량 (전부 판매 시 'all' 입력)") 
    async def se(self,i:discord.Interaction,t:str,s:str):
        await i.response.defer() # ephemeral=False (모두에게 보이기)
        u=i.user.id
        
        t_upper=t.upper()
        STATUS_NAMES = ["개떡상", "떡상", "주목", "개떡락", "떡락", "관심", "안정적"]
        
        found_t=None
        
        # 1. 주식 이름 확인 (우선 순위)
        for ticker, data in ST.items():
            if data['n'].upper() == t_upper:
                found_t=ticker
                break
                    
        # 2. 상태명 확인
        if not found_t and t_upper in [s.upper() for s in STATUS_NAMES]:
            target_status_name = t_upper
            matching_tickers = []
            
            all_s = g_all_s() 
            for ticker, price, delist_counter, daily_change_percent in all_s:
                current_status_name = self.g_ss_name(daily_change_percent).upper()
                
                if current_status_name == target_status_name:
                    matching_tickers.append(ticker)
            
            if len(matching_tickers) == 1:
                found_t = matching_tickers[0]
            elif len(matching_tickers) > 1:
                ticker_list = ", ".join([f"{ST[mt]['n']} ({mt})" for mt in matching_tickers])
                await i.followup.send(f"⚠️ **'{t}'** 상태를 가진 주식이 여러 개 있습니다 ({ticker_list}). 주식 이름으로 정확히 지정해 주세요.")
                return
            
        # 3. 티커 입력을 허용하지 않음 (이름이나 상태명이 아닌 경우 거부)
        if not found_t:
            await i.followup.send("❌ 존재하지 않는 주식 이름 또는 상태입니다.");return
        
        t=found_t
        
        cs=g_us(u,t);
        if cs<=0:await i.followup.send(f"❌ **{ST[t]['n']}** 주식을 보유하고 있지 않습니다.");return
        ss=0
        if s.lower()=='all':ss=cs
        else:
            try:ss=int(s);
            except ValueError:await i.followup.send("❌ 수량은 숫자이거나 'all'이어야 합니다.");return
            if ss<=0:await i.followup.send("❌ 판매 수량은 1개 이상이어야 합니다.");return
        if ss>cs:await i.followup.send(f"❌ 보유 수량({cs}주)보다 많은 주식을 판매할 수 없습니다.");return
        p=g_sp(t)
        if p is None:await i.followup.send("❌ 이 주식은 현재 거래가 불가능합니다.");return
        r=p*ss;cb=g_b(u);s_b(u,cb+r);u_us(u,t,-ss)
        # ephemeral=False로 변경하여 모두에게 보이게 함
        await i.followup.send(f"✅ **{i.user.display_name}** 님이 **{ST[t]['n']}** 주식 **{ss}주**를 **{fc(r)}**에 매도했습니다. 남은 보유: {g_us(u,t)}주")

    @sg.command(name="내포트폴리오", description="현재 보유한 주식 포트폴리오를 확인합니다.")
    async def sp(self,i:discord.Interaction):
        # 이 명령어는 사적인 정보이므로 ephemeral=True 유지
        await i.response.defer(ephemeral=True)
        p_list=g_p(i.user.id)
        if not p_list:await i.followup.send("❌ 현재 보유 중인 주식이 없습니다.");return
        e=discord.Embed(title="💼 내 주식 포트폴리오",color=discord.Color.green());tv=0.0
        for t,s in p_list:
            p=g_sp(t)
            if p:
                v=p*s;tv+=v;sn=ST.get(t,{}).get('n',t)
                e.add_field(name=f"{sn}",value=f"**{s:,}주** | 현재가: {fc(p)} | 평가액: {fc(v)}",inline=False)
        e.set_footer(text=f"총 포트폴리오 평가액: {fc(tv)}");await i.followup.send(embed=e)

if __name__ == "__main__":B().run(T)
