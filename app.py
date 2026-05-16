# CS Pro — Contrast Sensitivity Analyser
# Copyright (c) 2026 Dr Zain Khatib. All rights reserved.
# Unauthorised copying, modification, or redistribution of this software
# is strictly prohibited. This file is proprietary and confidential.
import base64 as _b64
_d=lambda s:_b64.b64decode(s).decode()
_AE='collapsed'
_AD='isi_active'
_AC='Log Contrast Sensitivity'
_AB='gratings_output'
_AA='Custom (enter DPI)'
_A9='doctor_email'
_A8='doctor_name'
_A7='score_d'
_A6='score_c'
_A5='score_b'
_A4='score_a'
_A3='gender'
_A2='_device_fp'
_A1='screen_valid'
_A0='distance_cm'
_z='screen_dpi'
_y='white'
_x='#f97316'
_w='#94a3b8'
_v='#0ea5e9'
_u='overall_ok'
_t='ppd'
_s='Severely reduced'
_r='Moderately reduced'
_q='Mildly reduced'
_p='Normal'
_o='56-75'
_n='20-55'
_m='activated_at'
_l='Visit'
_k='log_d'
_j='log_c'
_i='log_b'
_h='log_a'
_g='mrn'
_f='age'
_e='admin_authed'
_d='#e2e8f0'
_c='ok'
_b='lower'
_a='upper'
_Z='sd'
_Y='device_fingerprint'
_X='PATCH'
_W='licence_ok'
_V='--'
_U='#22c55e'
_T='rows'
_S='primary'
_R='licence_msg'
_Q='notes'
_P='is_active'
_O='name'
_N='aulcsf'
_M='licence_key'
_L='visit_date'
_K='visit_label'
_J='—'
_I='mean'
_H='D'
_G='C'
_F='eye'
_E='B'
_D='A'
_C=None
_B=False
_A=True
import streamlit as st,pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt,datetime,json,os,random,io,base64,time,hashlib,secrets,string,urllib.request
from PIL import Image
SUPABASE_URL=st.secrets['SUPABASE_URL']
SUPABASE_KEY=st.secrets['SUPABASE_KEY']
ADMIN_PASSWORD=st.secrets['ADMIN_PASSWORD']
def _sb_request(method,path,body=_C):
	import json as B;D=f"{SUPABASE_URL}/rest/v1/{path}";E=B.dumps(body).encode()if body else _C;A=urllib.request.Request(D,data=E,method=method);A.add_header('apikey',SUPABASE_KEY);A.add_header('Authorization',f"Bearer {SUPABASE_KEY}");A.add_header('Content-Type','application/json');A.add_header('Prefer','return=representation')
	try:
		with urllib.request.urlopen(A,timeout=6)as F:C=F.read().decode();return B.loads(C)if C.strip()else[]
	except Exception as G:return{'error':str(G)}
def generate_licence_key():A=string.ascii_uppercase+string.digits;B=[''.join(secrets.choice(A)for B in range(4))for B in range(3)];return'CSPRO-'+'-'.join(B)
def fetch_licence(key):
	A=_sb_request('GET',f"cspro_licences?licence_key=eq.{key}&select=*")
	if isinstance(A,list)and A:return A[0]
def activate_licence(key,fingerprint):A=datetime.datetime.utcnow().isoformat();_sb_request(_X,f"cspro_licences?licence_key=eq.{key}",{_Y:fingerprint,_m:A})
def check_licence(key,fingerprint):
	C=fingerprint;A=key
	if not A:return _B,'Enter your licence key to access CS Pro.'
	B=fetch_licence(A)
	if B is _C:return _B,'❌ Invalid licence key. Please check and try again.'
	if not B.get(_P,_B):return _B,'❌ This licence has been revoked. Contact Dr Zain Khatib.'
	D=B.get(_Y)
	if not D:activate_licence(A,C);return _A,'✅ Licence activated on this device.'
	if D!=C:return _B,'❌ This licence key is already activated on another device. Licence keys cannot be shared. Contact Dr Zain Khatib for a new key.'
	return _A,'✅ Licence valid.'
def admin_create_licence(doctor_name,doctor_email,notes):
	B=generate_licence_key();A=_sb_request('POST','cspro_licences',{_M:B,_A8:doctor_name,_A9:doctor_email,_Q:notes})
	if isinstance(A,list)and A:return B,_C
	return _C,str(A.get('error','Unknown error'))
def admin_revoke_licence(key):_sb_request(_X,f"cspro_licences?licence_key=eq.{key}",{_P:_B})
def admin_reactivate_licence(key):_sb_request(_X,f"cspro_licences?licence_key=eq.{key}",{_P:_A})
def admin_list_licences():return _sb_request('GET','cspro_licences?select=*&order=created_at.desc')
st.set_page_config(page_title='CS Pro — Contrast Sensitivity Analyser',page_icon='👁️',layout='wide',initial_sidebar_state='expanded')
st.markdown('\n<style>\n@import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap\');\nhtml, body, [class*="css"] { font-family: \'Inter\', sans-serif; }\n/* Hide GitHub icon and Fork button in Streamlit toolbar */\na[href*="github.com"] { display: none !important; }\nbutton[title="Fork this app on GitHub"] { display: none !important; }\n[data-testid="stToolbar"] a { display: none !important; }\n[data-testid="stDecoration"] { display: none !important; }\nheader [data-testid="stToolbar"] { right: 0; }\n/* Hide any element linking to GitHub */\n.st-emotion-cache-zq5wmm { display: none !important; }\n.st-emotion-cache-1dp5vir { display: none !important; }\ndiv[data-testid="metric-container"] {\n    background: white; border: 1px solid #e2e8f0;\n    border-radius: 10px; padding: 14px 18px;\n    box-shadow: 0 1px 3px rgba(0,0,0,0.06);\n}\n[data-testid="stSidebar"] { background: #1e293b !important; }\n[data-testid="stSidebar"] * { color: #e2e8f0 !important; }\n[data-testid="stSidebar"] input,\n[data-testid="stSidebar"] textarea,\n[data-testid="stSidebar"] select,\n[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] *,\n[data-testid="stSidebar"] .stTextInput input,\n[data-testid="stSidebar"] .stNumberInput input {\n    color: #1e293b !important;\n    background-color: #f8fafc !important;\n    border-color: #cbd5e1 !important;\n}\n[data-testid="stSidebar"] ::placeholder {\n    color: #64748b !important;\n    opacity: 1 !important;\n}\n.stDownloadButton > button {\n    background-color: #0ea5e9 !important; color: white !important;\n    border: none !important; border-radius: 8px !important;\n    font-weight: 500 !important; width: 100%;\n}\n.section-hdr {\n    font-size: 15px; font-weight: 600; color: #1e293b;\n    margin-bottom: 12px; padding-bottom: 6px;\n    border-bottom: 2px solid #0ea5e9;\n}\n</style>\n',unsafe_allow_html=_A)
LOG_CS={_D:{1:1.,2:1.17,3:1.34,4:1.49,5:1.63,6:1.78,7:1.93,8:2.08},_E:{1:1.21,2:1.38,3:1.55,4:1.7,5:1.84,6:1.99,7:2.14,8:2.29},_G:{1:.91,2:1.08,3:1.25,4:1.4,5:1.54,6:1.69,7:1.84,8:1.99},_H:{1:.47,2:.64,3:.81,4:.96,5:1.1,6:1.25,7:1.4,8:1.55}}
LINEAR_CS={_D:[5,10,15,22,31,43,61,85,120],_E:[8,16,24,36,50,70,99,138,193],_G:[4,8,12,18,25,35,50,70,99],_H:[1.5,3,4.5,7,9.5,13,18,25,36]}
SPATIAL_FREQS=[3,6,12,18]
LOG_SPATIAL_FREQS=[np.log10(A)for A in SPATIAL_FREQS]
ROW_LABELS=[_D,_E,_G,_H]
ROW_NAMES={_D:'3 cpd',_E:'6 cpd',_G:'12 cpd',_H:'18 cpd'}
SCORES_ALL=['S','1','2','3','4','5','6','7','8']
CYCLES_IN_MASTER={_D:5,_E:8,_G:12,_H:16}
FREQS={_D:3,_E:6,_G:12,_H:18}
MASTER_DPI=1200
AGE_NORMS={_n:{_I:[1.84,2.09,1.76,1.33],_Z:[.14,.16,.17,.19]},_o:{_I:[1.56,1.8,1.5,.93],_Z:[.15,.165,.15,.25]}}
def score_to_log(row,score):
	A=score
	if not A:return
	return LOG_CS[row].get(int(A))
def calc_aulcsf(log_vals):
	A=log_vals
	if all(A is _C for A in A):return
	B=[A if A is not _C else .0 for A in A];C=sum((B[A]+B[A+1])/2*(LOG_SPATIAL_FREQS[A+1]-LOG_SPATIAL_FREQS[A])for A in range(len(LOG_SPATIAL_FREQS)-1));return round(C,3)
def interpret_aulcsf(val):
	A=val
	if A is _C:return'Insufficient data','gray'
	if A>=1.32:return _p,'green'
	if A>=1.19:return _q,'orange'
	if A>=1.09:return _r,'red'
	return _s,'darkred'
def get_norm_band(grp):A=AGE_NORMS[grp];return{_a:[A+B for(A,B)in zip(A[_I],A[_Z])],_I:A[_I],_b:[max(0,A-B)for(A,B)in zip(A[_I],A[_Z])]}
COMMON_SCREENS={'Samsung Galaxy Book4 Pro 360 (16")':212,'MacBook Pro 14" (M-series)':254,'MacBook Pro 16" (M-series)':254,'MacBook Air 13" (M-series)':224,'MacBook Air 15" (M-series)':224,'Dell XPS 13 (2560×1600)':227,'Dell XPS 15 (3456×2160)':261,'HP Spectre x360 14"':260,'Lenovo ThinkPad X1 Carbon (14")':210,'Surface Laptop 5 (13.5")':201,'Surface Pro 9 (13")':267,'iPad Pro 12.9" (M-series)':264,'iPad Air 11" (M3)':264,'Full HD Laptop 15.6" (1920×1080)':141,'Full HD Laptop 14" (1920×1080)':157,'2K Laptop 14" (2560×1600)':214,_AA:_C}
def ppd(dpi,dist_cm):A=2.54/dpi;return 1./np.degrees(np.arctan(A/dist_cm))
def circle_diam_px(freq_cpd,dpi,dist_cm,cycles):return max(60,int(round(ppd(dpi,dist_cm)/freq_cpd*cycles)))
def validate_screen(dpi,dist_cm):
	C=dist_cm;B=dpi;A={_t:round(ppd(B,C),1),_T:{}}
	for D in ROW_LABELS:E=FREQS[D];H=CYCLES_IN_MASTER[D];F=circle_diam_px(E,B,C,H);G=ppd(B,C)/E;I=G>=2. and F>=60;A[_T][D]={'freq':E,'diam_px':F,'ppc':round(G,1),_c:I}
	A[_u]=all(A[_c]for A in A[_T].values());return A
GRATING_DIR=os.path.join(os.path.dirname(__file__),_AB,'gratings')
BLANK_DIR=os.path.join(os.path.dirname(__file__),_AB,'blanks')
GRATINGS_AVAILABLE=os.path.isdir(GRATING_DIR)
def linear_to_srgb(L):return(np.power(np.clip(L,0,1),1/2.2)*255).astype(np.uint8)
def make_grating_image(freq_cpd,michelson,diam_px,cycles):A=diam_px;E=np.linspace(0,cycles*2*np.pi,A);F=np.tile(E,(A,1));C=.5*(1+michelson*np.sin(F));G=D=A//2;H,I=np.ogrid[:A,:A];C[np.sqrt((I-D)**2+(H-G)**2)>D-1]=.5;B=linear_to_srgb(C);return Image.fromarray(np.stack([B,B,B],axis=-1),mode='RGB')
def make_blank_image(diam_px):B=diam_px;A=int(linear_to_srgb(np.array([.5]))[0]);return Image.new('RGB',(B,B),(A,A,A))
@st.cache_data(show_spinner=_B)
def get_grating(row,score_label,diam_px):
	C=score_label;B=diam_px;A=row
	if GRATINGS_AVAILABLE:
		D=os.path.join(GRATING_DIR,f"grating_{A}{C}.png")
		if os.path.exists(D):return Image.open(D).resize((B,B),Image.LANCZOS)
	E=SCORES_ALL.index(C);F=LINEAR_CS[A][E];G=1./F;return make_grating_image(FREQS[A],G,B,CYCLES_IN_MASTER[A])
@st.cache_data(show_spinner=_B)
def get_blank(row,diam_px):
	A=diam_px
	if GRATINGS_AVAILABLE:
		B=os.path.join(BLANK_DIR,f"blank_{row}.png")
		if os.path.exists(B):return Image.open(B).resize((A,A),Image.LANCZOS)
	return make_blank_image(A)
def generate_pdf(patient_name,patient_age,patient_gender,patient_mrn,tests):
	p='sec';o='100%';d=patient_age;c='GRID';b='LEFTPADDING';a='BOTTOMPADDING';Z='TOPPADDING';Y='BACKGROUND';X='FONTSIZE';N=tests;L='Helvetica';J='FONTNAME';I='Helvetica-Bold';from reportlab.lib.pagesizes import A4;from reportlab.lib import colors as C;from reportlab.lib.units import cm as A;from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle as G;from reportlab.platypus import SimpleDocTemplate as q,Paragraph as H,Spacer as K,Table as O,TableStyle as P,HRFlowable as e,Image as r,KeepTogether as s;from reportlab.lib.enums import TA_CENTER as t;f=C.HexColor(_v);Q=C.HexColor('#1e293b');g=C.HexColor('#f1f5f9');R=C.HexColor(_w);A6=C.HexColor(_U);A7=C.HexColor('#f59e0b');A8=C.HexColor(_x);A9=C.HexColor('#ef4444');S=io.BytesIO();u=q(S,pagesize=A4,leftMargin=2*A,rightMargin=2*A,topMargin=2*A,bottomMargin=2*A);B=[];B.append(H('CS Pro',G('h',fontSize=20,textColor=f,fontName=I)));B.append(H('Contrast Sensitivity Function Report',G('s',fontSize=9,textColor=R,fontName=L,spaceAfter=4)));B.append(e(width=o,thickness=1,color=f));B.append(K(1,.4*A));v=[[patient_name,f"Age: {d} yrs · {patient_gender.capitalize()}",f"MRN: {patient_mrn or _J}",f"Date: {datetime.date.today().strftime("%d %b %Y")}"]];h=O(v,colWidths=[5*A,5*A,4*A,4*A]);h.setStyle(P([(J,(0,0),(-1,-1),L),(J,(0,0),(0,0),I),(X,(0,0),(-1,-1),9),(Y,(0,0),(-1,-1),g),(Z,(0,0),(-1,-1),6),(a,(0,0),(-1,-1),6),(b,(0,0),(-1,-1),8),(c,(0,0),(-1,-1),.5,C.HexColor(_d))]));B.append(h);B.append(K(1,.5*A))
	if N:
		w,E=plt.subplots(figsize=(8,4.2),dpi=140);T=np.arange(4);U=get_norm_band(_n if d<56 else _o);E.fill_between(T,U[_b],U[_a],color=_U,alpha=.12,label='Normal range (±1 SD)');E.plot(T,U[_I],color=_U,lw=1,ls=_V,alpha=.5);i=[_v,_x,'#8b5cf6','#10b981'];x={'OD':'-','OS':_V}
		for(y,D)in enumerate(N):
			F=[D.get(f"log_{A.lower()}")for A in ROW_LABELS];z,j=zip(*[(B,A)for(B,A)in enumerate(F)if A is not _C])if any(A is not _C for A in F)else([],[])
			if j:A0=i[y%len(i)];E.plot(list(z),list(j),color=A0,ls=x.get(D[_F],'-'),lw=2.2,marker='o',ms=7,markerfacecolor=_y,markeredgewidth=2,label=f"{D[_F]} · {D.get(_K)or D[_L]}")
		E.set_xticks(T);E.set_xticklabels([f"{A} cpd"for A in SPATIAL_FREQS]);E.set_ylim(0,2.6);E.set_ylabel(_AC);E.set_xlabel('Spatial Frequency (cpd)');E.grid(_A,color=_d,lw=.8);E.spines[['top','right']].set_visible(_B);E.legend(fontsize=8);plt.tight_layout();V=io.BytesIO();plt.savefig(V,format='png',bbox_inches='tight');plt.close(w);V.seek(0);B.append(s([H('Contrast Sensitivity Function Curve',G(p,fontSize=11,textColor=Q,fontName=I,spaceAfter=6)),r(V,width=16*A,height=9*A)]));B.append(K(1,.5*A))
	B.append(H('Detailed Scores',G(p,fontSize=11,textColor=Q,fontName=I,spaceAfter=8)))
	for D in N:
		W=D.get(_N);A1,_=interpret_aulcsf(W);B.append(H(f"<b>{D[_F]}</b> · {D.get(_K)or""} · {D[_L]}",G('te',fontSize=10,fontName=L,spaceAfter=4)));A2=[['Row','Freq','Score','Log CS','Status']];k=[]
		for M in ROW_LABELS:l=D.get(f"score_{M.lower()}");F=D.get(f"log_{M.lower()}");A3='Good'if F and F>=1.7 else'Borderline'if F and F>=1.4 else'Reduced'if F else'Not seen';k.append([M,ROW_NAMES[M],str(l)if l else'0',f"{F:.2f}"if F else _J,A3])
		m=O(A2+k,colWidths=[1.5*A,3*A,3*A,3*A,4.5*A]);m.setStyle(P([(J,(0,0),(-1,0),I),(J,(0,1),(-1,-1),L),(X,(0,0),(-1,-1),9),(Y,(0,0),(-1,0),Q),('TEXTCOLOR',(0,0),(-1,0),C.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[g,C.white]),(c,(0,0),(-1,-1),.5,C.HexColor(_d)),(Z,(0,0),(-1,-1),5),(a,(0,0),(-1,-1),5),(b,(0,0),(-1,-1),6),('ALIGN',(2,0),(-1,-1),'CENTER')]));B.append(m);A5=[[f"AULCSF: {W:.3f}"if W else'AULCSF: —',A1,f"Notes: {D.get(_Q)or _J}"]];n=O(A5,colWidths=[4*A,4*A,10*A]);n.setStyle(P([(J,(0,0),(0,0),I),(J,(1,0),(-1,0),L),(X,(0,0),(-1,-1),9),(Y,(0,0),(-1,-1),C.HexColor('#f0f9ff')),(c,(0,0),(-1,-1),.5,C.HexColor('#bae6fd')),(Z,(0,0),(-1,-1),5),(a,(0,0),(-1,-1),5),(b,(0,0),(-1,-1),6)]));B.append(n);B.append(K(1,.4*A))
	B.append(e(width=o,thickness=.5,color=R));B.append(K(1,.2*A));B.append(H(f"CS Pro · Generated {datetime.datetime.now().strftime("%d %b %Y %H:%M")} · Log CS: VectorVision CSV-1000 norms · AULCSF: Applegate et al.",G('ft',fontSize=7,textColor=R,alignment=t)));u.build(B);S.seek(0);return S.getvalue()
MAX_DISPLAY_PX=420
MIN_DISPLAY_PX=50
def pil_to_b64(img,size_px):A=size_px;C=img.resize((A,A),Image.LANCZOS);B=io.BytesIO();C.save(B,format='PNG');return base64.b64encode(B.getvalue()).decode()
def show_circle(img,label,physics_px):B=label;A=int(np.clip(physics_px,MIN_DISPLAY_PX,MAX_DISPLAY_PX));C=pil_to_b64(img,A);st.markdown(f'''
        <div style="text-align:center; margin-bottom:8px;">
          <div style="font-weight:600; font-size:15px; margin-bottom:6px; color:#1e293b;">{B}</div>
          <img src="data:image/png;base64,{C}"
               style="width:{A}px; height:{A}px;
                      border-radius:50%; display:inline-block;
                      box-shadow: 0 2px 8px rgba(0,0,0,0.15);"
               alt="{B}" />
        </div>
        ''',unsafe_allow_html=_A)
def init_state():
	B={'patients':{},'active_patient':_C,'tests':{},_z:96,_A0:200,_A1:validate_screen(96,200),'test_row_idx':0,'test_score_idx':0,'test_answers':{},'test_scores':{},'test_grating_pos':{},'test_done':_B,'test_started':_B,_AD:_B}
	for(A,C)in B.items():
		if A not in st.session_state:st.session_state[A]=C
init_state()
def _get_server_fingerprint():
	try:from streamlit.web.server.websocket_headers import _get_websocket_headers as C;A=C();B='|'.join([A.get('User-Agent',''),A.get('Accept-Language',''),A.get('Accept-Encoding','')])
	except Exception:B='fallback'
	return'fp'+hashlib.md5(B.encode()).hexdigest()[:12]
if _A2 not in st.session_state:st.session_state[_A2]=_get_server_fingerprint()
_fingerprint=st.session_state[_A2]
_params=st.query_params
_admin_mode=_params.get('admin','')=='1'
if _M not in st.session_state:st.session_state[_M]=''
if _W not in st.session_state:st.session_state[_W]=_B
if _R not in st.session_state:st.session_state[_R]=''
if _e not in st.session_state:st.session_state[_e]=_B
if _admin_mode:
	st.markdown('## 🔐 CS Pro Admin — Licence Manager')
	if not st.session_state[_e]:
		pwd=st.text_input('Admin password',type='password',key='admin_pwd_input')
		if st.button('Login',type=_S):
			if pwd==ADMIN_PASSWORD:st.session_state[_e]=_A;st.rerun()
			else:st.error('❌ Wrong password.')
		st.stop()
	st.markdown('### ➕ Generate New Licence')
	with st.form('gen_form'):col1,col2=st.columns(2);d_name=col1.text_input('Doctor name',placeholder='Dr Ravi Sharma');d_email=col2.text_input('Email (optional)',placeholder='doctor@clinic.com');d_notes=st.text_input('Notes (optional)',placeholder='Purchased batch 1');submitted=st.form_submit_button('🎫 Generate Key',type=_S,use_container_width=_A)
	if submitted:
		if not d_name.strip():st.error('Doctor name is required.')
		else:
			new_key,err=admin_create_licence(d_name.strip(),d_email.strip(),d_notes.strip())
			if new_key:st.success(f"✅ Licence created!");st.code(new_key,language=_C);st.info(f"Send this key to **{d_name}**. It activates on first use and locks to their device.")
			else:st.error(f"❌ Error: {err}")
	st.divider();st.markdown('### 📊 All Licences')
	if st.button('🔄 Refresh',key='admin_refresh'):st.rerun()
	licences=admin_list_licences()
	if isinstance(licences,list)and licences:
		for lic in licences:
			status_icon='🟢'if lic.get(_P)else'🔴';activated='✅ Activated'if lic.get(_m)else'⏳ Not yet used'
			with st.expander(f"{status_icon} {lic[_A8]} — {lic[_M]}"):
				st.markdown(f"**Email:** {lic.get(_A9)or _J}");st.markdown(f"**Status:** {"Active"if lic.get(_P)else"🔴 Revoked"}");st.markdown(f"**Device:** {activated}");st.markdown(f"**Fingerprint:** `{lic.get(_Y)or"none"}`");st.markdown(f"**Created:** {lic["created_at"][:10]}");st.markdown(f"**Notes:** {lic.get(_Q)or _J}");c1,c2,c3=st.columns(3)
				if lic.get(_P):
					if c1.button('🔴 Revoke',key=f"rev_{lic["id"]}"):admin_revoke_licence(lic[_M]);st.success('Revoked.');st.rerun()
				elif c1.button('🟢 Reactivate',key=f"react_{lic["id"]}"):admin_reactivate_licence(lic[_M]);st.success('Reactivated.');st.rerun()
				if c2.button('🖱️ Reset device lock',key=f"reset_{lic["id"]}",help='Clears fingerprint so key can be used on a new device'):_sb_request(_X,f"cspro_licences?licence_key=eq.{lic[_M]}",{_Y:_C,_m:_C});st.success('🔄 Device lock reset. Key can be activated on a new device.');st.rerun()
	else:st.info('No licences yet. Generate one above.')
	st.stop()
if not st.session_state[_W]:
	_,col,_=st.columns([1,2,1])
	with col:
		st.markdown('\n        <div style="text-align:center; padding: 40px 0 20px;">\n          <span style="font-size:56px;">👁️</span>\n          <h1 style="margin:12px 0 4px; font-size:28px; font-weight:700;">CS Pro</h1>\n          <p style="color:#64748b; font-size:15px; margin:0;">Contrast Sensitivity Analyser</p>\n          <p style="color:#64748b; font-size:13px; margin-top:4px;">VectorVision CSV-1000 Protocol</p>\n        </div>\n        ',unsafe_allow_html=_A);st.markdown('#### Enter your licence key');key_input=st.text_input('Licence key',placeholder='CSPRO-XXXX-XXXX-XXXX',key='licence_key_input',label_visibility=_AE).strip().upper()
		if st.button('🔓 Unlock CS Pro',type=_S,use_container_width=_A):ok,msg=check_licence(key_input,_fingerprint);st.session_state[_W]=ok;st.session_state[_M]=key_input;st.session_state[_R]=msg;st.rerun()
		if st.session_state[_R]:
			if st.session_state[_W]:st.success(st.session_state[_R])
			else:st.error(st.session_state[_R])
		st.markdown('<div style="text-align:center; margin-top:24px; color:#94a3b8; font-size:12px;">\n        Licences are single-device only and cannot be shared.<br>\n        Contact <b>Dr Zain Khatib</b> to obtain a licence key.\n        </div>',unsafe_allow_html=_A)
	st.stop()
with st.sidebar:
	st.markdown('## 👁️ CS Pro');st.caption('Near Vision Contrast Sensitivity');st.divider();st.markdown('### 🖥️ Screen Setup');screen_choice=st.selectbox('Screen type',list(COMMON_SCREENS.keys()),key='screen_choice')
	if screen_choice==_AA:dpi=st.number_input('DPI / PPI',min_value=60,max_value=600,value=96,step=1)
	else:dpi=COMMON_SCREENS[screen_choice];st.caption(f"DPI: **{dpi}**")
	dist_cm=st.number_input('Testing distance (cm)',min_value=30,max_value=200,value=50,step=5,key='distance_cm_input');val=validate_screen(dpi,dist_cm);st.session_state[_z]=dpi;st.session_state[_A0]=dist_cm;st.session_state[_A1]=val
	if val[_u]:st.success(f"✅ Valid · {val[_t]} px/°")
	else:bad=[A for(A,B)in val[_T].items()if not B[_c]];st.warning(f"⚠️ Rows {", ".join(bad)} may not render accurately at this distance")
	with st.expander('Circle sizes'):
		for row in ROW_LABELS:rv=val[_T][row];icon='✅'if rv[_c]else'⚠️';st.caption(f"{icon} Row {row} ({rv["freq"]}cpd): **{rv["diam_px"]}px**")
	st.divider();st.markdown('### Add Patient')
	with st.form('add_patient',clear_on_submit=_A):
		p_name=st.text_input('Full Name *',placeholder='e.g. Ramesh Kumar');p_age=st.number_input('Age *',min_value=1,max_value=120,value=45);p_gender=st.selectbox('Gender *',['Male','Female','Other']);p_mrn=st.text_input('MRN / ID',placeholder='OPH-2026-001')
		if st.form_submit_button('➕ Add Patient',use_container_width=_A):
			if p_name.strip():
				key=p_mrn.strip()or p_name.strip();st.session_state.patients[key]={_O:p_name.strip(),_f:int(p_age),_A3:p_gender,_g:p_mrn.strip()}
				if key not in st.session_state.tests:st.session_state.tests[key]=[]
				st.session_state.active_patient=key;st.success(f"Added {p_name}")
	st.divider();st.markdown('### Select Patient')
	if st.session_state.patients:keys=list(st.session_state.patients.keys());labels=[f"{st.session_state.patients[A][_O]}"for A in keys];idx=st.selectbox('Patient',range(len(keys)),format_func=lambda i:labels[i],key='patient_selector');st.session_state.active_patient=keys[idx]
	else:st.info('No patients yet.')
	st.divider();st.caption('VectorVision CSV-1000 protocol · 4 spatial frequencies')
if not st.session_state.active_patient:st.markdown('## Welcome to CS Pro');st.markdown('\n**CS Pro** is a contrast sensitivity testing tool based on the VectorVision CSV-1000 protocol, designed to run on any modern laptop at testing distances of **50 cm to 200 cm**.\n\n**Getting started:**\n1. **Select your laptop model** in the sidebar — sets the correct DPI automatically\n2. **Set screen brightness to 50%** before starting — critical for accurate results\n3. **Add a patient** using the sidebar form\n4. Go to **🔬 Live Test** tab to run the sinusoidal grating test\n5. Or use **📝 Manual Entry** to type in scores from a physical chart\n6. **📈 CS Graph** shows the contrast sensitivity curve with age-norm bands\n7. **⬇️ Download PDF** for the full clinical report\n    ');st.info('👈 Select your laptop model and set screen brightness to 50%, then add a patient to begin.');st.stop()
pk=st.session_state.active_patient
patient=st.session_state.patients[pk]
tests_list=st.session_state.tests.get(pk,[])
col_h,col_dl=st.columns([3,1])
with col_h:st.markdown(f"## {patient[_O]}");st.caption(f"{patient[_f]} yrs · {patient[_A3]}"+(f" · `{patient[_g]}`"if patient.get(_g)else''))
with col_dl:
	if tests_list:pdf_bytes=generate_pdf(patient[_O],patient[_f],patient[_A3],patient.get(_g,''),tests_list);st.download_button('⬇️ Download PDF Report',data=pdf_bytes,file_name=f"CVPRO_{patient[_O].replace(" ","_")}_{datetime.date.today()}.pdf",mime='application/pdf',use_container_width=_A)
st.divider()
tab_live,tab_manual,tab_chart,tab_history=st.tabs(['🔬 Live Test','📝 Manual Entry','📈 CS Graph','📋 Test History'])
with tab_live:
	dpi=st.session_state[_z];dist_cm=st.session_state[_A0];scr_val=st.session_state[_A1];st.markdown('<p class="section-hdr">🔬 Live Sinusoidal Grating Test</p>',unsafe_allow_html=_A)
	if scr_val[_u]:st.success(f"Screen: {dpi} DPI · {dist_cm} cm · {scr_val[_t]} px/° — All frequencies valid ✅")
	else:st.warning(f"⚠️ Screen setup may not render all frequencies accurately. Adjust distance in sidebar.")
	with st.expander('📋 Pre-test checklist — expand before starting'):st.markdown('\n| Item | Requirement |\n|---|---|\n| Testing distance | **50 cm – 200 cm** from laptop screen (adjustable in sidebar) |\n| Screen brightness | **50%** — do NOT exceed; higher brightness causes false positives |\n| Room lighting | Normal ambient indoor light (no direct glare on screen) |\n| Screen angle | Tilt screen so patient sees it straight-on, no reflections |\n| Patient correction | Best corrected vision — use appropriate correction for the selected distance |\n| Eye being tested | Occlude other eye with palm or occluder |\n| Adaptation | 30 seconds in room light before starting |\n| Screen preset | Select your exact laptop model in the sidebar |\n        ')
	with st.expander('🔬 Scientific basis — how CS Pro generates authentic gratings'):st.markdown("\n## How CS Pro Produces Clinically Valid Contrast Sensitivity Gratings\n\n### The core question: can a laptop screen replace a ₹7 lakh calibrated chart?\n\nThe answer lies in understanding what the CSV-1000 actually tests — and replicating that precisely in software.\n\n---\n\n### Step 1 — The screen as a calibrated ruler\n\nEvery modern laptop display is a physical grid of pixels, and the size of each pixel is fixed by the manufacturer.\nFrom the screen's **DPI (dots per inch)** — which we know precisely for each device — we can calculate the physical width of one pixel:\n\n> **Pixel size = 2.54 cm ÷ DPI**\n\nOn a Samsung Galaxy Book4 Pro (212 DPI), each pixel is **0.01198 cm wide** — about 0.12 mm. This is a fixed, known quantity, as precise as any ruler.\n\n---\n\n### Step 2 — Converting pixels to degrees of visual angle\n\nContrast sensitivity is measured in **cycles per degree (cpd)** of visual angle. The visual angle subtended by one pixel depends on how far the eye is from the screen:\n\n> **Pixels per degree = 1 ÷ arctan(pixel size ÷ viewing distance)**\n\nAt the default 50 cm on the Samsung Galaxy Book4 Pro (example calculation):\n\n> 1 ÷ arctan(0.01198 ÷ 50) = **72.8 pixels per degree**\n\nThis means we know, to sub-pixel accuracy, how many pixels correspond to one degree of visual angle at your testing distance.\n\n---\n\n### Step 3 — Computing the exact grating diameter\n\nFor each spatial frequency, we calculate how many pixels are needed to display exactly the right number of cycles across the correct visual angle:\n\n> **Grating diameter (px) = (pixels per degree ÷ frequency in cpd) × number of cycles**\n\nFor Row A (3 cpd) at 50 cm on the Galaxy Book4 Pro (example):\n\n> (72.8 ÷ 3) × 5 = **121 pixels**\n\nThis grating subtends exactly the correct visual angle — the same 3 cpd stimulus that the CSV-1000 presents, now computed from first principles.\n\n---\n\n### Step 4 — Mathematically pure sine wave luminance\n\nThe luminance of each pixel across the grating follows a true sinusoidal function:\n\n> **L(x) = 0.5 × (1 + C × sin(2π · f · x))**\n\nWhere **C** is the Michelson contrast — taken directly from VectorVision's published CSV-1000 normative data (e.g., Row B position 8 has a linear CS of 193, so C = 1/193 = 0.0052).\n\nThere are **no hard edges, no square waves, no harmonic distortion** — only a single pure spatial frequency, identical in mathematical form to what the CSV-1000 projects.\n\n---\n\n### Step 5 — Gamma correction ensures physical accuracy\n\nA pixel value of 128 (mid-grey) does not produce half the light output of 255 (white) — screens are non-linear. Without correction, the sine wave would be distorted in physical luminance.\n\nCS Pro applies the **standard sRGB gamma correction (γ = 2.2)** to every pixel before display:\n\n> **Pixel value = (L)^(1/2.2) × 255**\n\nThis ensures that what the screen physically emits is a true sinusoidal luminance pattern — not just a sinusoidal pixel value pattern. This is the same correction applied in laboratory-grade psychophysics software.\n\n---\n\n### Step 6 — Identical contrast values to CSV-1000\n\nThe Michelson contrast at each of the 36 test positions is taken directly from VectorVision's published linear CS norms. The scoring system, log CS values, AULCSF calculation, and age-normative bands are all identical to those used with the physical CSV-1000 chart.\n\n---\n\n### What is different from the CSV-1000\n\n| Factor | CSV-1000 | CS Pro |\n|---|---|---|\n| Grating physics | Sinusoidal ✅ | Sinusoidal ✅ |\n| Contrast values | VectorVision norms ✅ | Identical ✅ |\n| Spatial frequency accuracy | Hardware calibrated | Computed from DPI + distance ✅ |\n| Luminance | Fixed 85 cd/m² (backlit) | ~80–100 cd/m² at 50% brightness ⚠ |\n| Testing distance | 200 cm (far vision) | 50 – 200 cm (adjustable) ✅ |\n| Scoring & norms | Same | Identical ✅ |\n\nThe most meaningful difference is **luminance**. Luminance is controlled by standardising screen brightness at 50%. CS Pro supports testing distances from **50 cm to 200 cm** — adjust in the sidebar to match your clinical setup. Results at near distances (50–80 cm) reflect near vision contrast sensitivity and should not be directly equated to far-distance CSV-1000 scores without acknowledging this difference. At 200 cm, results are directly comparable to the standard CSV-1000 protocol.\n        ")
	st.divider()
	if not st.session_state.test_started:
		eye_choice=st.selectbox('Eye to test',['OD (Right eye)','OS (Left eye)'],key='live_eye_choice');visit_label=st.text_input('Visit label',placeholder='e.g. Pre-op, Post-op 1M',key='live_visit_label')
		if st.button('▶️ Start Test',type=_S,use_container_width=_B):
			st.session_state.test_started=_A;st.session_state.test_row_idx=0;st.session_state.test_score_idx=0;st.session_state.test_answers={};st.session_state.test_scores={};st.session_state.test_done=_B;st.session_state.test_eye=eye_choice.split()[0];st.session_state.test_visit_label=visit_label;pos={};last=_C;run=0
			for row in ROW_LABELS:
				for sc in SCORES_ALL:
					choices=[_D,_E]
					if run>=3:choices=[_E if last==_D else _D]
					side=random.choice(choices);pos[row,sc]=side;run=run+1 if side==last else 1;last=side
			st.session_state.test_grating_pos=pos;st.rerun()
	elif st.session_state.test_done:
		st.success('✅ Test complete!');scores_idx=st.session_state.test_scores;final={};log_vals=[]
		for row in ROW_LABELS:idx=scores_idx.get(row,0);clinical=idx;final[row]=clinical;log_vals.append(score_to_log(row,clinical))
		aulcsf=calc_aulcsf(log_vals);interp_label,_=interpret_aulcsf(aulcsf);c1,c2,c3,c4=st.columns(4);badge_map={_p:'🟢',_q:'🟡',_r:'🟠',_s:'🔴'}
		for(col,row)in zip([c1,c2,c3,c4],ROW_LABELS):lv=score_to_log(row,final[row]);col.metric(f"Row {row} · {ROW_NAMES[row]}",str(final[row])if final[row]else'0',f"logCS {lv:.2f}"if lv else'Not seen')
		if aulcsf:st.markdown(f"### AULCSF: `{aulcsf:.3f}` {badge_map.get(interp_label,"⚪")} {interp_label}")
		col_save,col_restart=st.columns(2)
		with col_save:
			if st.button('💾 Save to Patient Record',type=_S,use_container_width=_A):test_rec={_L:str(datetime.date.today()),_K:st.session_state.get('test_visit_label',''),_F:st.session_state.get('test_eye','OD'),_A4:final[_D],_A5:final[_E],_A6:final[_G],_A7:final[_H],_h:score_to_log(_D,final[_D]),_i:score_to_log(_E,final[_E]),_j:score_to_log(_G,final[_G]),_k:score_to_log(_H,final[_H]),_N:aulcsf,_Q:''};st.session_state.tests[pk].insert(0,test_rec);st.session_state.test_started=_B;st.session_state.test_done=_B;st.success('Saved! Switch to CS Graph or Test History to view.')
		with col_restart:
			if st.button('🔄 Restart Test',use_container_width=_A):st.session_state.test_started=_B;st.session_state.test_done=_B;st.rerun()
	else:
		if st.session_state.get(_AD,_B):st.session_state.isi_active=_B;isi_slot=st.empty();isi_slot.markdown('\n                <div style="\n                    display:flex; flex-direction:column;\n                    align-items:center; justify-content:center;\n                    height:320px; gap:32px;\n                ">\n                  <div style="display:flex; gap:80px;">\n                    <div style="\n                        width:180px; height:180px; border-radius:50%;\n                        background:#d1d5db;\n                        box-shadow:inset 0 2px 8px rgba(0,0,0,0.08);\n                    "></div>\n                    <div style="\n                        width:180px; height:180px; border-radius:50%;\n                        background:#d1d5db;\n                        box-shadow:inset 0 2px 8px rgba(0,0,0,0.08);\n                    "></div>\n                  </div>\n                  <div style="color:#94a3b8; font-size:13px; letter-spacing:0.05em;">next stimulus loading…</div>\n                </div>\n                ',unsafe_allow_html=_A);time.sleep(.45);isi_slot.empty();st.rerun()
		row_idx=st.session_state.test_row_idx;score_idx=st.session_state.test_score_idx
		if row_idx>=len(ROW_LABELS):st.session_state.test_done=_A;st.rerun()
		row=ROW_LABELS[row_idx];score=SCORES_ALL[score_idx];freq=FREQS[row];diam=circle_diam_px(freq,dpi,dist_cm,CYCLES_IN_MASTER[row]);pos=st.session_state.test_grating_pos.get((row,score),_D);done=row_idx*9+score_idx;st.progress(done/36,text=f"Row {row} ({ROW_NAMES[row]}) — Position {score}/8");grating_img=get_grating(row,score,diam);blank_img=get_blank(row,diam);img_A=grating_img if pos==_D else blank_img;img_B=grating_img if pos==_E else blank_img;display_px=int(np.clip(diam,MIN_DISPLAY_PX,MAX_DISPLAY_PX));st.markdown('### Which circle has the **stripes**?');st.caption(f"Row {row} · {freq} cpd · Position {score} · Michelson contrast: {1/LINEAR_CS[row][score_idx]:.4f} · Circle: {display_px}px ({dist_cm} cm, {dpi} DPI)");col_a,col_b=st.columns(2)
		with col_a:show_circle(img_A,_D,diam)
		with col_b:show_circle(img_B,_E,diam)
		st.markdown('#### Patient response:');b1,b2,b3,b4=st.columns(4)
		def record(response):
			A=response;B=A==pos;st.session_state.test_answers[row,score]={'response':A,'correct':B}
			if B:st.session_state.test_scores[row]=score_idx
			C=score_idx+1
			if C>=len(SCORES_ALL):st.session_state.test_row_idx+=1;st.session_state.test_score_idx=0
			else:st.session_state.test_score_idx=C
			st.session_state.isi_active=_A
		with b1:
			if st.button('🅰️  Circle A',use_container_width=_A,key=f"a_{row}{score}"):record(_D);st.rerun()
		with b2:
			if st.button('🅱️  Circle B',use_container_width=_A,key=f"b_{row}{score}"):record(_E);st.rerun()
		with b3:
			if st.button('❌ Neither',use_container_width=_A,key=f"n_{row}{score}"):record('neither');st.rerun()
		with b4:
			if st.button('⏭️ Next Row',use_container_width=_A,key=f"s_{row}{score}"):st.session_state.test_row_idx+=1;st.session_state.test_score_idx=0;st.session_state.isi_active=_A;st.rerun()
		if score=='S':st.info('ℹ️ This is the **sample grating** — the stripes are clearly visible. Use this to show the patient what to look for.')
with tab_manual:
	st.markdown('<p class="section-hdr">📝 Manual Score Entry</p>',unsafe_allow_html=_A)
	with st.form('manual_entry',clear_on_submit=_A):
		c1,c2,c3=st.columns(3)
		with c1:visit_date=st.date_input('Date',value=datetime.date.today())
		with c2:eye=st.selectbox('Eye',['OD (Right)','OS (Left)']);eye_code=eye.split()[0]
		with c3:visit_label=st.text_input('Visit Label',placeholder='Pre-op / Post-op 1M')
		st.markdown('#### Scores — enter last correct position for each row');sc1,sc2,sc3,sc4=st.columns(4);scores={}
		for(col,row)in zip([sc1,sc2,sc3,sc4],ROW_LABELS):
			with col:
				st.markdown(f"**Row {row}** · {ROW_NAMES[row]}");scores[row]=st.selectbox(f"Score {row}",list(range(9)),format_func=lambda x:'0 — not seen'if x==0 else str(x),key=f"m_score_{row}",label_visibility=_AE);lv=score_to_log(row,scores[row])
				if lv:st.caption(f"logCS: **{lv:.2f}**")
		notes=st.text_area('Clinical Notes',placeholder='e.g. NS4 cataract · Post Phaco')
		if st.form_submit_button('✅ Save',use_container_width=_A,type=_S):log_vals=[score_to_log(A,scores[A])for A in ROW_LABELS];aulcsf=calc_aulcsf(log_vals);rec={_L:str(visit_date),_K:visit_label.strip(),_F:eye_code,_A4:scores[_D],_A5:scores[_E],_A6:scores[_G],_A7:scores[_H],_h:log_vals[0],_i:log_vals[1],_j:log_vals[2],_k:log_vals[3],_N:aulcsf,_Q:notes.strip()};st.session_state.tests[pk].insert(0,rec);interp,_=interpret_aulcsf(aulcsf);st.success(f"Saved · AULCSF: {aulcsf:.3f} — {interp}"if aulcsf else'Saved')
with tab_chart:
	st.markdown('<p class="section-hdr">📈 Contrast Sensitivity Function Curve</p>',unsafe_allow_html=_A)
	if not tests_list:st.info('Record at least one test to generate the CSF curve.')
	else:
		t_labels=[f"{A[_F]} · {A.get(_K)or _l} · {A[_L]}"for A in tests_list];sel=st.multiselect('Select tests to display (max 4)',range(len(tests_list)),default=list(range(min(2,len(tests_list)))),format_func=lambda i:t_labels[i],max_selections=4);show_y=st.checkbox('Show 20–55 yr norm band',value=_A);show_o=st.checkbox('Show 56–75 yr norm band',value=_A)
		if sel:
			fig,ax=plt.subplots(figsize=(10,5.5),dpi=130);ax.set_facecolor('#f8fafc');fig.patch.set_facecolor(_y);xi=np.arange(4)
			if show_y:b=get_norm_band(_n);ax.fill_between(xi,b[_b],b[_a],color=_U,alpha=.13,label='Normal 20–55 yrs');ax.plot(xi,b[_I],color=_U,lw=1.2,ls=_V,alpha=.6)
			if show_o:b=get_norm_band(_o);ax.fill_between(xi,b[_b],b[_a],color=_w,alpha=.1,label='Normal 56–75 yrs');ax.plot(xi,b[_I],color=_w,lw=1.2,ls=_V,alpha=.5)
			pal=[_v,_x,'#8b5cf6','#10b981'];ls_map={'OD':'-','OS':_V}
			for(i,ti)in enumerate(sel):
				t=tests_list[ti];lv=[t.get(f"log_{A.lower()}")for A in ROW_LABELS];pts=[(B,A)for(B,A)in enumerate(lv)if A is not _C]
				if pts:
					px2,py=zip(*pts);ax.plot(list(px2),list(py),color=pal[i%4],ls=ls_map.get(t[_F],'-'),lw=2.5,marker='o',ms=8,markerfacecolor=_y,markeredgewidth=2.2,label=f"{t[_F]} — {t.get(_K)or _l} ({t[_L]})",zorder=5)
					for(px3,py3)in pts:ax.annotate(f"{py3:.2f}",(px3,py3),textcoords='offset points',xytext=(0,10),fontsize=8,color=pal[i%4],ha='center',fontweight='600')
			ax.set_xticks(xi);ax.set_xticklabels([f"{A} cpd"for A in SPATIAL_FREQS],fontsize=11);ax.set_ylim(0,2.7);ax.set_yticks([0,.5,1,1.5,2,2.5]);ax.set_ylabel(_AC,fontsize=11);ax.set_xlabel('Spatial Frequency (Cycles per Degree)',fontsize=11);ax.grid(_A,color=_d,lw=.8,alpha=.8);ax.spines[['top','right']].set_visible(_B);ax.legend(fontsize=9,loc='upper right',framealpha=.95);ax.set_title(f"{patient[_O]} ({patient[_f]} yrs)",fontsize=12,fontweight='600',color='#1e293b');plt.tight_layout();st.pyplot(fig,use_container_width=_A);plt.close(fig);st.markdown('#### AULCSF');badge_map={_p:'🟢',_q:'🟡',_r:'🟠',_s:'🔴'};cols=st.columns(len(sel))
			for(col,ti)in zip(cols,sel):t=tests_list[ti];v=t.get(_N);interp,_=interpret_aulcsf(v);col.metric(f"{t[_F]} · {t.get(_K)or t[_L]}",f"{v:.3f}"if v else _J,f"{badge_map.get(interp,"⚪")} {interp}")
with tab_history:
	st.markdown('<p class="section-hdr">📋 Test History</p>',unsafe_allow_html=_A)
	if not tests_list:st.info('No tests recorded yet.')
	else:
		rows_data=[]
		for t in tests_list:interp,_=interpret_aulcsf(t.get(_N));rows_data.append({'Date':t[_L],'Eye':t[_F],_l:t.get(_K)or _J,'A (3cpd)':f"{t[_A4]} → {t[_h]:.2f}"if t.get(_h)else'0','B (6cpd)':f"{t[_A5]} → {t[_i]:.2f}"if t.get(_i)else'0','C (12cpd)':f"{t[_A6]} → {t[_j]:.2f}"if t.get(_j)else'0','D (18cpd)':f"{t[_A7]} → {t[_k]:.2f}"if t.get(_k)else'0','AULCSF':f"{t[_N]:.3f}"if t.get(_N)is not _C else _J,'Interpretation':interp,'Notes':t.get(_Q)or _J})
		df=pd.DataFrame(rows_data);st.dataframe(df,use_container_width=_A,hide_index=_A);csv=df.to_csv(index=_B).encode('utf-8');st.download_button('⬇️ Download CSV',csv,f"CVPRO_{patient[_O].replace(" ","_")}_tests.csv",'text/csv');st.markdown('---');del_idx=st.selectbox('Select test to delete',range(len(tests_list)),format_func=lambda i:f"{tests_list[i][_F]} · {tests_list[i].get(_K)or _l} · {tests_list[i][_L]}")
		if st.button('🗑️ Delete',type='secondary'):st.session_state.tests[pk].pop(del_idx);st.rerun()
st.markdown('---')
st.markdown("<div style='text-align:center; color:#94a3b8; font-size:12px; line-height:2;'>CS Pro · Near Vision Contrast Sensitivity · Log CS: VectorVision CSV-1000 norms · AULCSF: Applegate et al. · <span style='color:#94a3b8;'>For research &amp; clinical use</span><br>For scientific basis of grating generation, open the <b>🔬 Scientific basis</b> section in the Live Test tab.</div>",unsafe_allow_html=_A)