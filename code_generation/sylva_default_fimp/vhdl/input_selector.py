# coding: utf8

''' Input selector VHDL FIMP code template '''

code_template = '''{% for lib, packages in libraries.items() %}Library {{ lib }};
{% for package in packages %}Use {{ lib }}.{{ package }}; {% endfor %}
  {% endfor %}
entity {{ name }} is
  port (
    clk : in std_logic;
    nrst : in std_logic{% for port in input_ports %};
    {{port.name}} : in {{port.type.name}}{% endfor %}{% for port in output_ports %};
    {{port.name}} : out {{port.type.name}}{% endfor %});
end {{ name }};

architecture fimp_0 of {{ name }} is
  {% for address_port in read_address_ports %}
  signal {{address_port.name}}_signal : {{address_port.type.name}};{% endfor %}

begin
  {% for address_port in read_address_ports %}
  {{address_port.name}} <= {{address_port.name}}_signal;{% endfor %}
  {% for cm in control_map %}
  -- Assign data input to data output {{cm.output_port.name}}
  process (clk, nrst{% for port in control_ports %}, {{port.name}}{% endfor %})
  begin
    if (nrst = '0') then
      {{cm.output_port.name}} <= {{cm.output_port.default}};
    elsif (rising_edge(clk)) then
      {% for condition in cm.conditions %}{% if loop.index0 == 0 %}{% for value in condition.valid_values %}{% if loop.index0 == 0 %}if ({{condition.control_port.name}} = {{value}}) then{% else %}elsif ({{condition.control_port.name}} = {{value}}) then{% endif %}
        {{cm.output_port.name}} <= {{condition.input_port.name}};
      {% endfor %}{% else %}{% for value in condition.valid_values %}elsif ({{condition.control_port.name}} = {{value}}) then
        {{cm.output_port.name}} <= {{condition.input_port.name}};
      {% endfor %}{% endif %}{% endfor %}end if;
    end if;
  end process;
  {% endfor %}
  -- Assign read address ports
  process (clk, nrst, {{current_cycle_port.name}})
  begin
    if (nrst = '0') then
      {% for address_port in read_address_ports %}
      {{address_port.name}}_signal <= {{address_port.default}};{% endfor %}

    elsif (rising_edge(clk)) then
      {% for address_port in read_address_ports %}
      case {{current_cycle_port.name}} is
        {% for action in address_port.actions %}
        when {{action.cycle}} =>
          {{address_port.name}}_signal <= {{action.address}};{% endfor %}
        when others =>
          {{address_port.name}}_signal <= {{address_port.name}}_signal;

      end case;
      {% endfor %}
    end if;
  end process;

end fimp_0;
'''
