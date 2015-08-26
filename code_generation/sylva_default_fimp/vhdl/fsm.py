# coding: utf8

''' FSM VHDL FIMP code template '''

code_template = '''{% for lib, packages in libraries.items() %}Library {{ lib }};
{% for package in packages %}Use {{ lib }}.{{ package }}; {% endfor %}
  {% endfor %}
entity {{ entity_name }} is
  port (
    clk : in std_logic;
    nrst : in std_logic;
    {{cycle_port.name}} : in {{cycle_port.type.name}};
    {{state_port.name}} : out {{state_port.type.name}});
end {{ entity_name }};

architecture fimp_0 of {{ entity_name }} is

  signal current_state : integer range 0 to {{ state_count - 1 }};
  signal next_state : integer range 0 to {{ state_count - 1 }};

begin

  -- synchronous state transaction
  process (clk, nrst)
  begin
    if (nrst = '0') then
      current_state <= {{ control.default_state.index }};
    elsif (rising_edge(clk)) then
      current_state <= next_state;
    end if;
  end process;

  -- asynchronous computation
  process (current_state, current_cycle)
  begin

    case current_state is
    {% for state in control.states %}
      when {{ state.index }} =>
        case current_cycle is {% for edge in state.edges %}
          when {{ edge.cycle }} =>
            next_state <= {{ edge.destination.index }}; {% endfor %}
          when others => next_state <= current_state;
        end case;
    {% endfor %}
      when others => next_state <= {{ control.default_state.index }};

    end case;

  end process;
end fimp_0;
'''
