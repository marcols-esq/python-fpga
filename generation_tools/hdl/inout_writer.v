module inout_writer #(
    parameter data_size = 8
) (
    inout [data_size - 1:0] INOUT,
    input [data_size - 1:0] IN,
    input WR_EN
);

assign INOUT = WR_EN ? IN : {data_size{1'bz}};

endmodule