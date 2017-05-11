# coding: utf-8
# The MIT License (MIT)

  # Copyright (c) 2014 by Shuo Li (contact@shuo.li)

  # Permission is hereby granted, free of charge, to any person obtaining a
  # copy of this software and associated documentation files (the "Software"),
  # to deal in the Software without restriction, including without limitation
  # the rights to use, copy, modify, merge, publish, distribute, sublicense,
  # and/or sell copies of the Software, and to permit persons to whom the
  # Software is furnished to do so, subject to the following conditions:

  # The above copyright notice and this permission notice shall be included in
  # all copies or substantial portions of the Software.

  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
  # DEALINGS IN THE SOFTWARE.

__author__ = 'Shuo Li <contact@shuol.li>'
__version__= '2014-06-17-08:40'

'''Templates to generate VHDL files
'''

interface = \
'''{{ license_header }}
{{ header }}
{% for lib, packages in libraries.items() %}Library {{ lib }};
{% for package in packages %}Use {{ lib }}.{{ package }}; {% endfor %}
{% endfor %}

entity {{ entity_name }} is
  {% if generics != [] %}
  generic (
  {% for g in generics %}  {{ g }}
  {% endfor %});{% endif %}{% if ports != [] %}
  port (
  {% for p in ports %}  {{ p }}
  {% endfor %});
  {% endif %}
end {{ entity_name }};
'''

architecture = \
'''architecture {{architecture_name}} of {{entity_name}} is

{% if components != [] %}{% for c in components %}{{c}}

{% endfor %}{% endif %}{% if signals != [] %}{% for s in signals %}  {{s}}
{% endfor %}{% endif %}
begin

{% if connections != [] %}{% for c in connections %}  {{c}}
{% endfor %}{% endif %}
{% if design_units != [] %}{% for u in design_units %}  {{u}}
{% endfor %}{% endif %}
end {{architecture_name}};
'''

component = \
'''  component {{entity_name}} is
    {% if generics != [] %}
    generic (
    {% for g in generics %}  {{g}}
    {% endfor %});{% endif %}{% if ports != [] %}
    port (
    {% for p in ports %}  {{p}}
    {% endfor %});{% endif %}
    end component;
'''

fsm = \
'''{{ license_header }}

library ieee;
use ieee.std_logic_1164.all;

entity fsm is
  generic (
    state_count : integer := {{ state_count }};
    max_condition : integer := {{ max_condition }}
  );
  port (
    clk : in std_logic;
    nrst : in std_logic;
    condition: in integer range 0 to max_condition;
    current_state : out integer range 0 to state_count - 1
  );
end fsm;
'''

fsm_fimp = \
'''
library ieee;
use ieee.std_logic_1164.all;

architecture fimp_{{ fimp_index }} of fsm is

  signal current_state_internal : integer range 0 to state_count - 1;

begin
  current_state <= current_state_internal;
  process (clk, nrst)
    begin
      if (nrst = '0') then
        current_state_internal <= 0;
      elsif (rising_edge(clk)) then
        case current_state_internal is {% for state in states %}
          when {{ state.current_state }} =>
            case condition is {% for condition in state.conditions %}
              when {{ condition.value }} =>
                current_state_internal <= {{ condition.next_state }}; {% endfor %}
              when others => current_state_internal <= current_state_internal;
            end case; {% endfor %}
          when others => current_state_internal <= 0;
        end case;
      end if;
    end process;
end fimp_{{ fimp_index }};
'''

input_selector = \
'''{{ license_header }}

library ieee;
library work;
use ieee.std_logic_1164.all;
use work.all;
use work.DataTokenTypes.all;

-- each port has one input selector
entity input_selector is
  generic (
    source_count : integer := {{ source_count }}
  );
  port (
    clk : in std_logic;
    nrst : in std_logic;
    data_in : in {{ output_type }}_vector(source_count - 1 downto 0);
    selection : in integer range 0 to source_count - 1;
    data_out : out {{ output_type }}
  );
end input_selector;

architecture fimp_0 of input_selector is

begin
  process (clk, nrst)
    begin
      if (nrst = '0') then
        data_out <= {{ default_output }};
      elsif (rising_edge(clk)) then
        data_out <= data_in(selection);
      end if;
    end process;
end fimp_0;
'''

ramp = \
'''{{ license_header }}

library ieee;
use ieee.std_logic_1164.all;

-- usable range : 0 to length - 1
entity ramp is
  generic (
    length : integer := {{ length }}
  );
  port (
    clk : in std_logic;
    nrst : in std_logic;
    value : out integer range 0 to length
  );
end ramp;

architecture fimp_0 of ramp is
  signal value_internal : integer range 0 to length;
begin
  value <= value_internal;
  process (clk, nrst)
    begin
      if (nrst = '0') then
        value_internal <= 0;
      elsif (rising_edge(clk)) then
        if (value_internal < length - 1) then
          value_internal <= value_internal + 1;
        else
          value_internal <= 0;
        end if;
      end if;
    end process;
end fimp_0;
'''

buffer_writer = \
'''{{ license_header }}

library ieee;
library work;
use ieee.std_logic_1164.all;
use work.all;
use work.DataTokenTypes.all;

-- usable range : 0 to length - 1
-- state
--   0 : idle
--   others : address_out + 1
entity buffer_writer_{{ DataTokenType }} is
  generic (
    buffer_size : integer := 16
  );
  port (
    clk : in std_logic;
    nrst : in std_logic;
    state_in : in integer range 0 to buffer_size;
    data_in : in {{ DataTokenType_string }};
    address_out : out integer range 0 to buffer_size - 1;
    write_en : out std_logic;
    data_out : out {{ DataTokenType_string }}
  );
end buffer_writer_{{ DataTokenType }};

architecture fimp_0 of buffer_writer_{{ DataTokenType }} is
  signal last_state : integer range 0 to buffer_size;
  constant default_data_out : {{ DataTokenType_string }} := {{ default_data_out }};
begin
  process (clk, nrst)
    begin
      if (nrst = '0') then
        address_out <= 0;
        write_en <= '0';
        data_out <= default_data_out;
        last_state <= 0;
      elsif (rising_edge(clk)) then
        if ( (state_in /= 0) and (state_in /= last_state) ) then
          address_out <= state_in - 1;
          write_en <= '1';
          data_out <= data_in;
          last_state <= state_in;
        else
          address_out <= 0;
          write_en <= '0';
          data_out <= default_data_out;
        end if;
      end if;
    end process;
end fimp_0;
'''

data_buffer = \
'''{{ license_header }}

library ieee;
library work;
use ieee.std_logic_1164.all;
use work.all;
use work.DataTokenTypes.all;

entity data_buffer_{{ DataTokenType }} is
  generic (
    buffer_size : integer := 16
  );
  port (
    clk : in std_logic;
    nrst : in std_logic;
    data_in : in {{ DataTokenType_string }};
    data_out : out {{ DataTokenType_string }};
    address_in : in integer range 0 to buffer_size - 1;
    write_en : in std_logic
  );
end data_buffer_{{ DataTokenType }};

architecture fimp_0 of data_buffer_{{ DataTokenType }} is
  constant default_data_out : {{ DataTokenType_string }} := {{ default_data_out }};
  signal content : {{ DataTokenType }}_vector(buffer_size - 1 downto 0);
begin
  process (clk, nrst)
    begin
      if (nrst = '0') then
        data_out <= default_data_out;
        content <= (others => default_data_out);
      elsif (rising_edge(clk)) then
        if write_en = '1' then
          content(address_in) <= data_in;
        else
          data_out <= content(address_in);
        end if;
      end if;
    end process;
end fimp_0;
'''

DataTokenTypes = \
'''{{ license_header }}

library ieee;
use ieee.std_logic_1164.all;

package DataTokenTypes is

  {% for type in types %}type {{ type.name }} is
  {{ type.definition }};
  {% endfor %}
  {% for type in sub_types %}subtype {{ type.name }} is
  {{ type.definition }};
  {% endfor %}

end DataTokenTypes;
'''
