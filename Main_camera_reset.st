
PROGRAM _INIT
	(* Insert code here *)
	resetacqcount:=AcqCnt;
	oldaccacq:=accacq;
END_PROGRAM

PROGRAM _CYCLIC
	(* Insert code here *)
	IF NOT(oldaccacq=accacq) THEN
		ImAcq:=FALSE;
		oldaccacq:=accacq;
		END_IF;
END_PROGRAM

PROGRAM _EXIT
	(* Insert code here *)
	 
END_PROGRAM

