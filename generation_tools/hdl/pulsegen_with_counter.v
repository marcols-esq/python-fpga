// module for generating N pulses to CLK

module cnt_pulsegen (
    input MAIN_CLK,
    input [7:0] CNT,
    input TRG,
    output CLK
);

reg [8:0] cnt;

always @(posedge MAIN_CLK)
begin
    if (TRG) begin
        cnt <= CNT + 1;
    end
    else if (cnt > 0) begin
        cnt <= cnt - 1;
    end 
end

assign CLK = TRG ? 1'b0 : ((cnt > 0) ? MAIN_CLK : 1'b0);

endmodule