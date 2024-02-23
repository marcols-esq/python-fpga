`timescale 1ns/100ps

module epp (
    input CLK,
    input [7:0] DATA_TX,
    inout [7:0] DB,
    input nASTB,
    input nDSTB,
    input nWRITE,
    output WAIT,
    output reg [7:0] ADDR,
    output reg [7:0] DATA_RX
);

parameter idle = 2'b00;
parameter read = 2'b01;
parameter write = 2'b10;

reg [7:0] data_bus;
reg [1:0] state;
reg [1:0] next_state;

initial 
begin
    state <= 2'b00;
    next_state <= 2'b00;
end

always @(posedge CLK)
begin
    state = next_state;
    case(state)
        idle:
            begin
                data_bus <= 8'hxx;
            end
        read:
            begin
                data_bus <= DATA_TX;
            end
        write:
            begin
                if (!nASTB) begin
                    ADDR <= DB;
                end
                else if (!nDSTB) begin
                    DATA_RX <= DB;
                end
            end
		  default: begin
		      data_bus <= 8'hxx;
		  end
    endcase
end

always @(*) begin
    case (state)
        idle: begin
            if (!nASTB || !nDSTB) begin
                next_state <= nWRITE ? read : write;
            end
            else begin
                next_state <= idle;
            end
        end
        read: begin
            if (nDSTB) begin
                next_state <= idle;
            end
            else begin
                next_state <= read;
            end
        end
        write: begin
            if (nDSTB && nASTB) begin
                next_state <= idle;
            end
            else begin
                next_state <= write;
            end
        end
        default: begin
            next_state <= idle;
        end
    endcase
end

assign WAIT = (state != idle);
assign DB = (!nDSTB && nWRITE) ? data_bus : 8'hzz;

endmodule