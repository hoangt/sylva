# coding: utf8

''' Output selector VHDL FIMP code template '''

code_template = '''{% for lib, packages in libraries.items() %}Library {{ lib }};
{% for package in packages %}Use {{ lib }}.{{ package }}; {% endfor %}
  {% endfor %}
entity {{ entity_name }} is
  port (
    clk : in std_logic;
    nrst : in std_logic{% for port in control_ports %};
    {{port[0]}} : in {{port[1]}}{% endfor %}{% for port in data_input_ports %};
    {{port[0]}} : in {{port[1]}}{% endfor %}{% for port in data_output_ports %};
    {{port[0]}} : out {{port[1]}}{% endfor %});
end {{ entity_name }};

architecture fimp_0 of {{ entity_name }} is

begin
  {% for cport in control_map %}
  process (clk, nrst, {{cport[0]}})
  begin

    if (nrst = '0') then
      {% for dport in cport[1] %}
      {{dport[0][0]}} <= {{dport[0][2]}};{% endfor %}

    elsif (rising_edge(clk)) then

      case {{cport[0]}} is

        when {{OUTPUT}} =>
          {% for dport in cport[1] %}
          {{dport[0][0]}} <= {{dport[1][0]}};{% endfor %}

        when {{IO}} =>
          {% for dport in cport[1] %}
          {{dport[0][0]}} <= {{dport[1][0]}};{% endfor %}

        when others =>
          {% for dport in cport[1] %}
          {{dport[0][0]}} <= {{dport[0][2]}};{% endfor %}

      end case;
    end if;
  end process;
  {% endfor %}
end fimp_0;
'''
