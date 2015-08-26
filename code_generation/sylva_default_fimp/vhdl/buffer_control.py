# coding: utf8

''' Buffer control VHDL FIMP code template '''

code_template = '''{% for lib, packages in libraries.items() %}Library {{ lib }};
{% for package in packages %}Use {{ lib }}.{{ package }}; {% endfor %}
  {% endfor %}
entity {{ entity_name }} is
  port (
    clk : in std_logic;
    nrst : in std_logic;
    {{current_cycle_port.name}} : in {{current_cycle_port.type.name}}{% for port in control_ports %};
    {{port[0].name}} : in {{port[0].type.name}}{% endfor %}{% for port in control_ports %};
    {{port[1].name}} : out {{port[1].type.name}}{% endfor %}{% for port in address_ports %};
    {{port.name}} : out {{port.type.name}}{% endfor %});
end {{ entity_name }};

architecture fimp_0 of {{ entity_name }} is

  {% for port in address_ports %}signal {{port.name}}_signal : {{port.type.name}};
  {% endfor %}
begin

  {% for port in address_ports %}{{port.name}} <= {{port.name}}_signal;
  {% endfor %}
  process(clk, nrst)
  begin
    if (nrst = '0') then

      {% for port in control_ports %}{{port[1].name}} <= '0';
      {% endfor %}{% for port in address_ports %}{{port.name}}_signal <= 0;
      {% endfor %}
    elsif (rising_edge(clk)) then
      {% for port in control_ports %}
      case {{port[0].name}} is
        when {{OUTPUT}} => {{port[1].name}} <= '1';
        when {{IO}} => {{port[1].name}} <= '1';
        when others => {{port[1].name}} <= '0';
      end case;
      {% endfor %}{% for port in address_ports %}
      case {{current_cycle_port.name}} is {% for action in port.actions %}
        when {{action[0]}} => {{port.name}}_signal <= {{action[1]}};{% endfor %}
        when others => {{port.name}}_signal <= {{port.name}}_signal;
      end case;
      {% endfor %}
    end if;
  end process;

end fimp_0;
'''
