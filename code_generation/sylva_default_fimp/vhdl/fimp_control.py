# coding: utf8

''' FIMP control VHDL FIMP code template '''

code_template = '''{% for lib, packages in libraries.items() %}Library {{ lib }};
{% for package in packages %}Use {{ lib }}.{{ package }}; {% endfor %}
  {% endfor %}
entity {{ entity_name }} is
  port (
    clk : in std_logic;
    nrst : in std_logic{% for port in input_ports %};
    {{port.name}} : in {{port.type.name}}{% endfor %};
    {{en_port.name}} : out {{en_port.type.name}});
end {{ entity_name }};

architecture fimp_0 of {{ entity_name }} is
  {% for port in input_ports %}
  signal en_{{port.name}} : {{en_port.type.name}};{% endfor %}

begin
  {% for port in input_ports %}
  en_{{port.name}} <= '0' when {{port.name}} = {{IDLE}} else '1';{% endfor %}

  {{en_port.name}} <= '0' {% for port in input_ports %}
    or en_{{port.name}}{% endfor %};

end fimp_0;
'''
