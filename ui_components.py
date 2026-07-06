import base64
import os

import streamlit as st
import streamlit.components.v1 as _stc

def _inject_loading_overlay():
    _stc.html("""<!DOCTYPE html><html><head><style>*{margin:0;padding:0;}body{background:transparent;overflow:hidden;}</style></head>
<body><script>
(function(){
  var doc=window.parent.document;
  if(!doc.getElementById('tld-ov')){
    var s=doc.createElement('style');
    s.textContent='@keyframes tld-spin{to{transform:rotate(360deg)}}@keyframes tld-pop{from{transform:scale(.75);opacity:0}to{transform:scale(1);opacity:1}}';
    doc.head.appendChild(s);
    var ov=doc.createElement('div');
    ov.id='tld-ov';
    ov.style.cssText='display:none;position:fixed;inset:0;z-index:2147483647;background:rgba(2,6,23,.72);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);align-items:center;justify-content:center';
    ov.innerHTML='<div style="background:linear-gradient(135deg,#0f4287,#2563eb 55%,#7c3aed);border-radius:18px;padding:28px 46px;display:flex;flex-direction:column;align-items:center;gap:14px;box-shadow:0 24px 54px rgba(0,0,0,.45);animation:tld-pop .22s cubic-bezier(.34,1.56,.64,1) both"><div style="width:42px;height:42px;border:4px solid rgba(255,255,255,.22);border-top-color:#fff;border-radius:50%;animation:tld-spin .7s linear infinite"></div><div style="color:#fff;font-size:21px;font-weight:900;font-family:Segoe UI,Arial,sans-serif;text-align:center">&#9203; Cargando Data</div><div style="color:rgba(255,255,255,.72);font-size:11px;font-weight:700;font-family:Segoe UI,Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;text-align:center">Dashboard Teletalk Digital &mdash; Por favor espere</div></div>';
    doc.body.appendChild(ov);
  }
  var ov=doc.getElementById('tld-ov');
  var timer=null;
  function show(){
    if(!ov) return;
    ov.style.display='flex';
    if(timer) clearTimeout(timer);
    timer=setTimeout(hide,1800);
  }
  function hide(){
    if(!ov) return;
    ov.style.display='none';
    if(timer) clearTimeout(timer);
    timer=null;
  }

  // Solo mostrar entre paginas/secciones del menu lateral.
  // No escucha el StatusWidget de Streamlit, porque eso se activa con filtros.
  if(!doc.__tldNavOverlayBound){
    doc.__tldNavOverlayBound=true;
    doc.addEventListener('click',function(e){
      var t=e.target;
      var menuItem=t.closest('section[data-testid="stSidebar"] .stRadio label');
      var sidebarPage=t.closest('[data-testid="stSidebarNavLink"]');
      if(menuItem || sidebarPage){ show(); }
    },true);
  }
  hide();
})();
</script></body></html>""",height=0,scrolling=False)


@st.cache_data(ttl=3600)
def _leer_img_b64(img_file):
    """Lee la imagen una sola vez y la cachea para no releerla en cada cambio de pestaña."""
    if not os.path.exists(img_file):
        return ""
    with open(img_file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = img_file.split(".")[-1].lower()
    mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
    return f'background-image: url("data:{mime};base64,{b64}");'

def set_bg(img_file):
    bg = _leer_img_b64(img_file)
    if not bg:
        st.sidebar.warning(f"Imagen no encontrada: {img_file}")
    st.markdown(f"""<style>
        .stApp {{ {bg} background-size:cover; background-position:center; background-attachment:fixed; }}
        .main-title {{ text-align:center; color:black; font-weight:900; font-size:52px; margin-bottom:6px; }}
        .sub-title {{ text-align:center; font-weight:700; font-size:20px; color:#004a99; margin-bottom:25px; }}
        .kpi-wrapper {{ display:flex; flex-direction:column; align-items:center; margin-top:20px; }}
        .box-header-dc {{ background:linear-gradient(135deg,#0f4287,#2563eb); color:white; width:320px; padding:18px 22px; border-radius:22px; text-align:center; font-weight:900; font-size:16px; margin-bottom:18px; box-shadow:0 18px 40px rgba(15,66,135,.18); letter-spacing:.08em; text-transform:uppercase; }}
        .box-header-tt {{ background:linear-gradient(135deg,#6d0b8c,#9333ea); color:white; width:320px; padding:18px 22px; border-radius:22px; text-align:center; font-weight:900; font-size:16px; margin-bottom:18px; box-shadow:0 18px 40px rgba(109,11,140,.18); letter-spacing:.08em; text-transform:uppercase; }}
        .data-card-dc {{ background-color:rgba(255,255,255,.96); width:320px; padding:24px; border-radius:24px; border:2px solid #0f4287; text-align:center; margin-bottom:16px; box-shadow:0 16px 40px rgba(0,0,0,.08); }}
        .data-card-tt {{ background-color:rgba(255,255,255,.96); width:320px; padding:24px; border-radius:24px; border:2px solid #6d0b8c; text-align:center; margin-bottom:16px; box-shadow:0 16px 40px rgba(0,0,0,.08); }}
        .label {{ color:#4b5563; font-weight:800; font-size:13px; text-transform:uppercase; display:block; letter-spacing:.1em; margin-bottom:8px; }}
        .value {{ color:#111827; font-size:42px; font-weight:900; display:block; line-height:1.05; }}
        .section-title-dc {{ color:#004a99; font-size:38px; font-weight:900; margin-bottom:10px; }}
        .section-title-tt {{ color:#70008f; font-size:38px; font-weight:900; margin-bottom:10px; }}
        .small-subtitle-dc {{ color:#004a99; font-weight:800; font-size:18px; margin-bottom:10px; }}
        .small-subtitle-tt {{ color:#70008f; font-weight:800; font-size:18px; margin-bottom:10px; }}
        .block-filter {{ background-color:rgba(255,255,255,.85); padding:16px; border-radius:16px; border:1px solid #d9d9d9; margin-top:20px; margin-bottom:20px; }}
        .stExpander {{ border-radius:12px !important; overflow:hidden; }}
    </style>""", unsafe_allow_html=True)
