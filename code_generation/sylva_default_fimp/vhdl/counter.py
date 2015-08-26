# coding: utf8

''' Counter VHDL FIMP code template '''

code_template = '''{% for lib, packages in libraries.items() %}Library {{ lib }};
{% for package in packages %}Use {{ lib }}.{{ package }}; {% endfor %}
  {% endfor %}
entity {{ name }} is
  port (
    clk : in std_logic;
    nrst : in std_logic;
    {{ current_cycle_port.name }} : out {{ current_cycle_port.type.name }});
end {{ name }};

architecture fimp_0 of {{ name }} is

  signal {{ current_cycle_port.name }}_signal : {{ current_cycle_port.type.name }};

begin

  {{ current_cycle_port.name }} <= {{ current_cycle_port.name }}_signal;

  process (clk, nrst)
  begin
    if (nrst = '0') then
      {{ current_cycle_port.name }}_signal <= 0;
    elsif (rising_edge(clk)) then
      if ({{ current_cycle_port.name }}_signal < {{ max_value }} - 1) then
        {{ current_cycle_port.name }}_signal <= {{ current_cycle_port.name }}_signal + 1;
      else
        {{ current_cycle_port.name }}_signal <= 0;
      end if;
    end if;
  end process;

end fimp_0;
'''
