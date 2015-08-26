# coding: utf8

''' FIMP control VHDL FIMP code template '''

code_template = '''{% for lib, packages in libraries.items() %}Library {{ lib }};
{% for package in packages %}Use {{ lib }}.{{ package }}; {% endfor %}
  {% endfor %}
entity {{ entity_name }} is
  port (
    clk : in std_logic;
    nrst : in std_logic;
    {{wr_port.name}} : in {{wr_port.type.name}};
    {{write_address_port.name}} : in {{write_address_port.type.name}};
    {{read_address_port.name}} : in {{read_address_port.type.name}};
    {{data_input_port.name}} : in {{data_input_port.type.name}};
    {{data_output_port.name}} : out {{data_output_port.type.name}});
end {{ entity_name }};

architecture fimp_0 of {{ entity_name }} is

  type buffer_type is array (0 to {{buffer_size}}) of {{data_input_port.type.name}};
  signal buffer_content : buffer_type;

begin

  process (clk, nrst)
  begin

    if (nrst = '0') then

      {{data_output_port.name}} <= {{default_data_output}};

    elsif (rising_edge(clk)) then

      if ({{wr_port.name}} = '1') then
        buffer_content({{write_address_port.name}}) <= {{data_input_port.name}};
        {{data_output_port.name}} <= {{default_data_output}};
      else
        {{data_output_port.name}} <= buffer_content({{read_address_port.name}});
      end if;

    end if;
  end process;
end fimp_0;

'''
