"use strict";
const $ = (id) => document.getElementById(id);
const MONTHS = ["январь","февраль","март","апрель","май","июнь","июль","август","сентябрь","октябрь","ноябрь","декабрь"];
const TYPE_NAMES = {workday:"Рабочий",weekend:"Выходной",holiday:"Праздник"};
const country = $("country"); const year = $("year"); const month = $("month");
const notice = $("notice");
function selected() {
  const value = {country:country.value,year:Number(year.value),month:Number(month.value)};
  if (!Number.isInteger(value.year)||value.year<2020||value.year>2040) throw new Error("Введите год от 2020 до 2040");
  if (!Number.isInteger(value.month)||value.month<1||value.month>12) throw new Error("Выберите месяц");
  return value;
}
function query(p){return new URLSearchParams(p).toString();}
function setNotice(message,isError=false){notice.hidden=false;notice.className="notice"+(isError?" error":"");notice.textContent=message;}
function hideNotice(){notice.hidden=true;}
async function api(path, options={}) {
  const response=await fetch(path,options);
  let json; try{json=await response.json();}catch(_){throw new Error("Сервер вернул некорректный ответ");}
  if(!response.ok)throw new Error(json?.detail||`HTTP ${response.status}`);
  return json;
}
function markBusy(busy){for(const id of ["fetch","db","save"])$(id).disabled=busy;}
async function perform(fn){markBusy(true);hideNotice();try{await fn();}catch(err){setNotice(`Ошибка: ${err.message}`,true);}finally{markBusy(false);}}
async function health(){try{await api("/api/health");$("status").textContent="● API И БД ДОСТУПНЫ";$("status").className="status";}catch(_){$("status").textContent="● НЕТ СОЕДИНЕНИЯ";$("status").className="status status-error";}}
function displayDate(value) {const [y,m,d]=value.split("-").map(Number);return new Date(y,m-1,d).toLocaleDateString("ru-RU",{day:"2-digit",month:"2-digit",year:"numeric"});}
function renderCalendar(result){
  $("calendar-empty").hidden=true;$("calendar-section").hidden=false;
  $("month-label").textContent=`${MONTHS[result.month-1].toUpperCase()} ${result.year} · ${result.country_name}`;
  $("stat-work").textContent=result.summary.workday;
  $("stat-weekend").textContent=result.summary.weekend;
  $("stat-holiday").textContent=result.summary.holiday;
  const grid=$("calendar-grid");grid.replaceChildren();
  const firstWeekDay = new Date(result.year,result.month-1,1).getDay();
  for(let i=0;i<(firstWeekDay+6)%7;i++){const blank=document.createElement("div");blank.className="calendar-spacer";grid.append(blank);}
  const list=$("holiday-list");list.replaceChildren();
  for(const day of result.days){
    const cell=document.createElement("div");cell.className=`calendar-cell ${day.day_type}`;
    const no=document.createElement("div");no.className="day-no";no.textContent=String(Number(day.date.slice(-2)));cell.append(no);
    if(day.holiday_name){const name=document.createElement("div");name.className="holiday-name";name.title=day.holiday_name;name.textContent=day.holiday_name;cell.append(name);
      const item=document.createElement("li");const when=document.createElement("strong");when.textContent=displayDate(day.date);const what=document.createElement("span");what.textContent=day.holiday_name;item.append(when,what);list.append(item);
    }
    grid.append(cell);
  }
  if(!list.childElementCount){const item=document.createElement("li");item.textContent="В этом месяце национальных праздников нет.";list.append(item);}
}
async function fetchCalendar(){const p=selected();const result=await api(`/api/calendar?${query(p)}`);renderCalendar(result);setNotice("Календарь получен: Frontend → Backend → отдельный Web-сервис.");}
async function fetchSaved(){
  const p=selected();const data=await api(`/api/saved?${query(p)}`);
  $("saved-total").textContent=`${data.total} записей`;
  $("saved-empty").hidden=data.total!==0;
  $("saved-table-wrap").hidden=data.total===0;
  $("saved-empty").textContent="В PostgreSQL пока нет записей за этот месяц. Нажмите «Сохранить месяц в БД».";
  const tbody=$("saved-body");tbody.replaceChildren();
  for(const item of data.entries){
    const tr=document.createElement("tr");
    const date=document.createElement("td");date.textContent=displayDate(item.day_date);
    const type=document.createElement("td");const tag=document.createElement("span");tag.className="tag "+item.day_type;tag.textContent=TYPE_NAMES[item.day_type]||item.day_type;type.append(tag);
    const name=document.createElement("td");name.textContent=item.holiday_name||"—";
    const note=document.createElement("td");note.className="note-cell";note.textContent=item.note||"—";
    const actions=document.createElement("td");
    const edit=document.createElement("button");edit.className="small-btn";edit.type="button";edit.textContent="Заметка";
    edit.addEventListener("click",()=>perform(async()=>{
      const newValue=window.prompt(`Заметка для ${displayDate(item.day_date)} (до 350 символов):`,item.note||"");
      if(newValue===null)return;
      if(newValue.length>350)throw new Error("Заметка слишком длинная (максимум 350 символов)");
      await api(`/api/saved/${item.id}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({note:newValue})});
      await fetchSaved();setNotice("Заметка обновлена в PostgreSQL (UPDATE).");
    }));
    const del=document.createElement("button");del.className="small-btn danger";del.type="button";del.textContent="Удалить";
    del.addEventListener("click",()=>perform(async()=>{
      if(!window.confirm(`Удалить запись ${displayDate(item.day_date)} из БД?`))return;
      await api(`/api/saved/${item.id}`,{method:"DELETE"});await fetchSaved();setNotice("Запись удалена из PostgreSQL (DELETE).");
    }));
    actions.append(edit,del);tr.append(date,type,name,note,actions);tbody.append(tr);
  }
  return data.total;
}
async function saveMonth(){
  const p=selected();const result=await api("/api/save-month",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(p)});
  await fetchSaved();setNotice(`Сохранено/обновлено ${result.saved} дней в PostgreSQL. Заметки сохранены.`);
}
$("fetch").addEventListener("click",()=>perform(fetchCalendar));
$("db").addEventListener("click",()=>perform(async()=>{const total=await fetchSaved();setNotice(`Получено ${total} записей непосредственно из PostgreSQL через Backend.`);}));
$("save").addEventListener("click",()=>perform(saveMonth));
(function init(){const now=new Date();year.value=String(Math.max(2020,Math.min(2040,now.getFullYear())));month.value=String(now.getMonth()+1);health();})();
