
PROGRAM _INIT
	(* Insert code here *)
	loopcount:=0; //Current number of loops
	amplSearch:=0; //Control variable for starting the amplitude search
	processdone:=0; //Initialize variable to 0
	OldAcqCnt:=AcqCnt; //Initialize variable
	ImAcq:=FALSE; // Set initial image acquisition
END_PROGRAM

PROGRAM _CYCLIC
	//We receive signal to start
	IF amplSearch>0 AND loopcount=0 THEN
		offset:=0; //offset reset
		delaynet:=systime+20000; //Scheduling the next picture based on systime + increment
		ImAcq := TRUE; //Enable taking picture
		loopcount:=1; //set loopcount
		processdone:=0;
	END_IF;
	
	//We are in the first loop after getting signal start, we already have a picture
	IF (AcqCnt>OldAcqCnt OR (OldAcqCnt=255 AND AcqCnt=0)  )AND (loopcount=1 OR loopcount=2) THEN
		hPosX:=0; //reset highest position of X 
		lPosX:=99999; //reset lowest position of X
		delaynet:=delaynet+1*(period);// Scheduling the next picture
		ImAcq := TRUE; //Enable taking picture
		OldAcqCnt:=OldAcqCnt+1; //increase count of images taken
		loopcount:=loopcount+1; //increase loop count
	END_IF;
	
	
	//We are in the 2+ loop after getting signal start, we have picture and initial data as well as a new picture
	IF (AcqCnt>OldAcqCnt OR (OldAcqCnt=255 AND AcqCnt=0)  )AND loopcount>2 THEN //The complicated conditions are needed for when the AcqCnt rolls over at 255
		IF PosX1 > hPosX THEN
			hPosX:=PosX1;
		END_IF; //if new X pos is higher than recorded highest, save it
		
		IF PosX1 <lPosX AND NOT(PosX1=0) THEN
			lPosX:=PosX1;
		END_IF; //if new X pos is lower than recorded lowest, save it

		delaynet:=delaynet+1*(period)+offsetincrement; // Scheduling the next picture (old time+period+increment)
		offset:=offset+offsetincrement; //increase offset
		OldAcqCnt:=OldAcqCnt+1; //increase count of images taken
		ImAcq := TRUE; //take picture
		loopcount:=loopcount+1; //increase loop count
	END_IF;
	
	//Measurement finished
	IF offset>(0.6*period) THEN //0.6 = 1.2 of period
		pampl:=hPosX-lPosX;
		IF NOT(loopcount=0) THEN
			processdone:=1;
		END_IF;
		amplSearch:=0;
		loopcount:=0;
		
	END_IF;


END_PROGRAM

PROGRAM _EXIT
	(* Insert code here *)
	 
END_PROGRAM
