-- Markdown extraktu → Word podle šablony TNK 136 (pandoc 2.9)
local function je_popisek(el)
  -- odstavec začínající tučným „Obr. N“ / „Tab. N“
  if el.t ~= 'Para' or #el.content < 1 or el.content[1].t ~= 'Strong' then return nil end
  local s = pandoc.utils.stringify(el.content[1])
  local v = s:match('^Výpis%s+(%d+)$')
  if v then return 'Výpis', v end
  local druh, cislo = s:match('^(%a+)%.%s*([%w%.]+)$')
  if druh == 'Obr' then return 'Obrázek', cislo end
  if druh == 'Tab' then return 'Tabulka', cislo end
  return nil
end

function RawBlock(el)
  if el.format == 'html' and el.text:match('<table') then
    return pandoc.read(el.text, 'html').blocks
  end
end

function Para(el)
  local druh, cislo = je_popisek(el)
  if druh then
    local zbytek = {}
    for i = 2, #el.content do table.insert(zbytek, el.content[i]) end
    while #zbytek > 0 and zbytek[1].t == 'Space' do table.remove(zbytek, 1) end
    local obsah = {pandoc.Str(druh .. ' ' .. cislo .. ' –'), pandoc.Space()}
    for _, x in ipairs(zbytek) do table.insert(obsah, x) end
    return pandoc.Div({pandoc.Para(obsah)}, pandoc.Attr('', {}, {['custom-style'] = 'NadpisTabObr'}))
  end
  if #el.content == 1 and el.content[1].t == 'Image' then
    return pandoc.Div({el}, pandoc.Attr('', {}, {['custom-style'] = 'Obrázek'}))
  end
  return pandoc.Div({el}, pandoc.Attr('', {}, {['custom-style'] = 'Text normy'}))
end

-- Tabulky převedené z Wordu mají často prázdný řádek záhlaví a skutečné záhlaví
-- v prvním řádku těla; ten se přesune do záhlaví.
function Table(tbl)
  local hlava = tbl.head.rows
  local prazdna = true
  for _, r in ipairs(hlava) do
    for _, c in ipairs(r.cells) do
      if pandoc.utils.stringify(c.contents) ~= '' then prazdna = false end
    end
  end
  if prazdna and #tbl.bodies > 0 and #tbl.bodies[1].body > 0 then
    local prvni = table.remove(tbl.bodies[1].body, 1)
    tbl.head.rows = {prvni}
  end
  return tbl
end
