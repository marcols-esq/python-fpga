`timescale 1ns / 100ps

module TV80_CPU (
	CLK, nCLR, CE, 
	ADDR, /*DI, DO,*/ DQ, nRD, nWR, nMREQ, nIORQ, 
	nBUSRQ, nBUSAK,
	nWAIT, nINT, nNMI,
	nM1, TS) ;
	
parameter RESET_VECTOR = 16'h0000;
parameter Mode = 1;    // 0 => Z80, 1 => Fast Z80, 2 => 8080, 3 => GB
parameter T2Write = 1; // 0 => wr_n active in T3, /=0 => wr_n active in T2
parameter IOWait  = 0; // 0 => Single cycle I/O, 1 => Std I/O cycle	

input CLK, nCLR, CE;
output [15:0] ADDR;
inout [7:0] DQ;
//input [7:0] DI;
//output [7:0] DO;
//Memor/IO control bus
output nRD, nWR, nMREQ, nIORQ;
reg nRD, nWR, nMREQ, nIORQ;
input nWAIT, nINT, nNMI, nBUSRQ;
output nBUSAK;
output nM1;
output [2:0] TS;

wire iorq, no_read, write, rfsh_n, halt_n; 
wire [15:0] A; 
wire [7:0] DO;  
wire [2:0] mc;
wire intcycle_n, IntE, stop;
//Inputs
wire wait_n, int_n, nmi_n, busrq_n; 


assign wait_n = nWAIT; //
reg [7:0] DI_REG;
	
//----------------------------------------------------------
//	 Z80 comatible CPU
//----------------------------------------------------------
tv80_core #(Mode, IOWait, RESET_VECTOR)CPU(
	// Outputs
	.m1_n(nM1),
	.iorq(iorq),
	.no_read(no_read),
	.write(write),
	.rfsh_n(rfsh_n),
	.halt_n(halt_n),
	.busak_n(nBUSAK),
	.A(A),
	.do(DO),
	.mc(mc),
	.ts(TS), 
	.intcycle_n(intcycle_n),
	.IntE(IntE),
	.stop(stop),
	// Inputs
	.reset_n(nCLR),
	.clk(CLK), 
	.cen(CE), 
	.wait_n(wait_n), 
	.int_n(int_n), 
	.nmi_n(nmi_n), 
	.busrq_n(busrq_n), 
	.dinst(DQ), 
	.di(DI_REG));
	
assign ADDR = A;
assign int_n = nINT;
assign nmi_n = nNMI;
assign busrq_n = nBUSRQ;
assign DQ = ~nWR ? DO : 8'hzz;
//assign D = DO;
//assign DINST = DI;
	
//----------------------------------------------------------
//	Interface controller
//----------------------------------------------------------  

always @(posedge CLK or negedge nCLR) begin
	if (!nCLR) begin
		nRD   <= #1 1'b1;
		nWR   <= #1 1'b1;
		nIORQ <= #1 1'b1;
		nMREQ <= #1 1'b1;
		DI_REG <= #1 8'd0;
	end
	else begin
		if(CE) begin
			nRD <= #1 1'b1;
			nWR <= #1 1'b1;
			nIORQ <= #1 1'b1;
			nMREQ <= #1 1'b1;
			if (mc == 3'b001) begin
				if (TS == 3'b001 || (TS == 3'b010 && wait_n == 1'b0))	begin
					nRD <= #1 ~intcycle_n;
					nMREQ <= #1 ~intcycle_n;
					nIORQ <= #1 intcycle_n;
				end
				`ifdef TV80_REFRESH
				if (tstate[3])
					nMREQ <= #1 1'b0;
				`endif
			end // if (mcycle[0])          
			else begin
				if ((TS == 3'b001 || (TS == 3'b010 && wait_n == 1'b0)) && no_read == 1'b0 && write == 1'b0) begin
					nRD <= #1 1'b0;
					nIORQ <= #1 ~iorq;
					nMREQ <= #1 iorq;
				end
				if (T2Write == 0) begin                          
					if (TS == 3'b010 && write == 1'b1)	begin
						nWR <= #1 1'b0;
						nIORQ <= #1 ~iorq;
						nMREQ <= #1 iorq;
					end
				end
				else begin
					if ((TS == 3'b001 || (TS == 3'b010 && wait_n == 1'b0)) && write == 1'b1) begin
						nWR <= #1 1'b0;
						nIORQ <= #1 ~iorq;
						nMREQ <= #1 iorq;
					end
				end // else: !if(T2write == 0)		
			end // else: !if(mcycle[0])
		end		
		//Data Input register
		if (TS == 3'b010 && wait_n == 1'b1)
			DI_REG <= #1 DQ;
	end // else: !if(!reset_n)
end // always @ (posedge clk or negedge reset_n)  

endmodule
